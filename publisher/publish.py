#!/usr/bin/env python3
"""Publish pre-signed resource packages from an exact repository commit. No signing secrets."""
import base64, hashlib, json, os, pathlib, re, subprocess, tempfile, urllib.error, urllib.parse, urllib.request, zipfile
REPO = 'lumicho111/rabbitkeeper-updatededicated'
MAX_PACKAGE = 512*1024*1024

def require(ok, message):
    if not ok: raise ValueError(message)

def validate_request(request):
    require(request.get('schema') == 1 and request.get('repository') == REPO, 'Wrong publication schema or repository')
    release = request['release']; tag = release['tag']
    require(isinstance(release.get('draft'), bool), 'Explicit draft flag required')
    require(bool(re.fullmatch(r'resource-[0-9]+', tag)) or (release['draft'] and bool(re.fullmatch(r'publisher-check-[A-Za-z0-9-]+', tag))), 'Invalid publication tag')
    require(isinstance(release.get('title'), str) and 0 < len(release['title']) <= 200, 'Invalid release title')
    require(isinstance(release.get('notes'), str) and len(release['notes']) <= 30000, 'Invalid release notes')
    require(len(request['assets']) == 1, 'This publisher accepts one signed resource ZIP per request')
    for asset in request['assets']:
        match = re.fullmatch(r'rabbit-float-build([0-9]+)-resource-([0-9]+)(?:-[A-Za-z0-9_-]+)?\.zip', asset['name'])
        require(match is not None, 'Unsupported resource filename')
        require(isinstance(asset['size'], int) and 0 < asset['size'] <= MAX_PACKAGE, 'Invalid package size')
        require(bool(re.fullmatch('[a-f0-9]{64}', asset['sha256'])), 'Invalid package hash')
        require(0 < len(asset['parts']) <= 2048, 'Invalid payload parts')
        for part in asset['parts']:
            require(bool(re.fullmatch(r'publisher/payloads/[A-Za-z0-9_-]+/[A-Za-z0-9_.-]+\.b64', part['path'])), 'Payload outside publication directory')
            require(bool(re.fullmatch('[a-f0-9]{64}', part['sha256'])), 'Invalid part hash')
    return request

def assemble(request, read_file, directory, key_bytes):
    key = directory/'public-key.pem'; key.write_bytes(key_bytes)
    outputs = []
    for asset in request['assets']:
        output = directory/asset['name']; size=0; digest=hashlib.sha256()
        with output.open('wb') as stream:
            for part in asset['parts']:
                raw = read_file(part['path'], 2*1024*1024)
                require(hashlib.sha256(raw).hexdigest() == part['sha256'], 'Payload part hash mismatch')
                data = base64.b64decode(raw, validate=True); size += len(data)
                require(size <= asset['size'] and size <= MAX_PACKAGE, 'Payload exceeds declared size')
                stream.write(data); digest.update(data)
        require(size == asset['size'] and digest.hexdigest() == asset['sha256'], 'Package download hash mismatch')
        with zipfile.ZipFile(output) as bundle:
            infos=bundle.infolist()
            require(len(infos)<=5002 and sum(info.file_size for info in infos)<=MAX_PACKAGE+2*1024*1024, 'ZIP expands beyond package limit')
            require(bundle.getinfo('manifest.json').file_size <= 1024*1024 and bundle.getinfo('manifest.sig').file_size <= 16384, 'Manifest or signature too large')
            raw = bundle.read('manifest.json'); signature=bundle.read('manifest.sig')
            manifest_path=directory/'manifest.json'; manifest_path.write_bytes(raw)
            signature_path=directory/'manifest.sig'; signature_path.write_bytes(signature)
            result=subprocess.run(['openssl','dgst','-sha256','-verify',str(key),'-signature',str(signature_path),str(manifest_path)],capture_output=True)
            require(result.returncode == 0, 'APK public-key signature verification failed')
            require(bundle.testzip() is None, 'Invalid ZIP CRC')
            manifest = json.loads(raw); match=re.fullmatch(r'rabbit-float-build([0-9]+)-resource-([0-9]+)(?:-[A-Za-z0-9_-]+)?\.zip',asset['name'])
            require(manifest.get('schema') == 1 and manifest.get('appId') == 'app.ii.phone', 'Wrong app package')
            require(manifest['nativeBuild'] == int(match[1]) and manifest['sequence'] == int(match[2]), 'Filename / signed version mismatch')
            if not request['release']['draft']:
                require(request['release']['tag'] == 'resource-'+str(manifest['sequence']).zfill(3), 'Release tag / signed version mismatch')
            names = bundle.namelist(); require(len(names) == len(set(names)) and len(names) <= 5002, 'Duplicate or excessive ZIP entries')
            for name in names:
                require(not name.startswith('/') and '\\' not in name and ':' not in name and all(p not in ('','.','..') for p in name.split('/')), 'Unsafe ZIP name')
                if name in ('manifest.json','manifest.sig'): continue
                require(name.startswith('www/') and name[4:] in manifest['files'], 'Undeclared resource entry')
                require(bundle.getinfo(name).file_size <= 128*1024*1024, 'Resource too large')
                with bundle.open(name) as content:
                    file_hash = hashlib.sha256()
                    for block in iter(lambda:content.read(1024*1024), b''): file_hash.update(block)
                require(file_hash.hexdigest() == manifest['files'][name[4:]], 'Signed resource hash mismatch')
        outputs.append((asset, output))
    return outputs

def publish(request, outputs, api, commit):
    wanted=request['release']; tag=wanted['tag']
    marker='<!-- rabbit-float-publisher:'+tag+' -->'
    notes=wanted['notes']+'\n\n'+marker
    releases=api('GET','/releases?per_page=100')
    matches=[r for r in releases if r['tag_name']==tag or (r['draft'] and marker in (r.get('body') or '')) or (r['draft'] and r['id']==wanted.get('existing_draft_id'))]
    require(len(matches)<=1, 'Ambiguous release tag')
    release=matches[0] if matches else api('POST','/releases',{'tag_name':tag,'target_commitish':commit,'name':wanted['title'],'body':notes,'draft':True,'prerelease':False})
    existing=api('GET',f"/releases/{release['id']}/assets?per_page=100")
    for asset, path in outputs:
        same=[a for a in existing if a['name']==asset['name']]
        require(len(same)<=1, 'Duplicate release attachment')
        if same:
            require(same[0].get('size')==asset['size'] and same[0].get('digest')=='sha256:'+asset['sha256'], 'Existing attachment differs; do not overwrite published versions')
        else:
            require(release['draft'], 'Cannot append to an already published release')
            uploaded=api('UPLOAD',f"/releases/{release['id']}/assets?name="+urllib.parse.quote(asset['name'],safe=''),path.read_bytes())
            require(uploaded.get('size')==asset['size'] and uploaded.get('digest')=='sha256:'+asset['sha256'], 'Uploaded attachment hash mismatch')
    if release['draft']:
        release=api('PATCH',f"/releases/{release['id']}",{'tag_name':tag,'name':wanted['title'],'body':notes,'draft':wanted['draft'],'prerelease':False,**({} if wanted['draft'] else {'make_latest':'true'})})
    else:
        require(not wanted['draft'], 'Public release exists; refusing to turn it into a draft')
    print(('Draft publication verified: ' if wanted['draft'] else 'Published: ')+release['html_url'])
    return release

class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self,*args,**kwargs): raise ValueError('Unexpected authenticated API redirect')

class Client:
    def __init__(self, repo, commit, token):
        require(repo==REPO and bool(re.fullmatch('[a-f0-9]{40}',commit)), 'Unexpected publication context')
        self.repo,self.commit,self.token=repo,commit,token
        self.opener=urllib.request.build_opener(NoRedirect())
    def call(self, method, path, data=None, raw=False, limit=8*1024*1024):
        base='https://uploads.github.com/repos/' if method=='UPLOAD' else 'https://api.github.com/repos/'
        headers={'Authorization':'Bearer '+self.token,'Accept':'application/vnd.github.raw+json' if raw else 'application/vnd.github+json','X-GitHub-Api-Version':'2022-11-28','User-Agent':'RabbitFloat-Release-Publisher'}
        if method=='UPLOAD': headers['Content-Type']='application/zip'; verb='POST';payload=data
        else: verb=method; payload=None if data is None else json.dumps(data,ensure_ascii=False).encode();headers['Content-Type']='application/json'
        req=urllib.request.Request(base+self.repo+path,data=payload,headers=headers,method=verb)
        with self.opener.open(req,timeout=90) as response:
            body=response.read(limit+1);require(len(body)<=limit,'API response too large')
            return body if raw else json.loads(body)
    def read(self, path, limit):
        return self.call('GET','/contents/'+urllib.parse.quote(path,safe='/')+'?ref='+self.commit,raw=True,limit=limit)

def main():
    client=Client(os.environ['GH_REPO'],os.environ['GH_COMMIT'],os.environ['GH_TOKEN'])
    try: raw=client.read('publisher/request.json',1024*1024)
    except urllib.error.HTTPError as error:
        if error.code==404: print('Publisher ready. No publication request yet.');return
        raise
    request=validate_request(json.loads(raw))
    with tempfile.TemporaryDirectory() as folder:
        outputs=assemble(request,client.read,pathlib.Path(folder),client.read('publisher/public-key.pem',16384))
        publish(request,outputs,client.call,client.commit)

if __name__=='__main__': main()
