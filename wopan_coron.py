import asyncio,aiohttp,time,math,os,requests,re,datetime,json
from requests_toolbelt  import MultipartEncoder
import numpy as np
from wopan import Wopan

class Tasker():
    def __init__(self, nTask=5, tSleep=1):
        self.nTask = nTask
        self.tSleep = tSleep

    def run(self, task_pool):

        async def main(tasks):
            outputs = await asyncio.gather(*tasks)
            return outputs

        s = []
        nTask = self.nTask
        tSleep = self.tSleep

        for i in range(int(np.ceil(len(task_pool)/nTask))):
            tasks = task_pool[i*nTask:(i+1)*nTask]
            outputs = asyncio.run(main(tasks))
            for output in outputs:
                s = s + output
            time.sleep(tSleep)

        return s

async def uploadPart(fid, data,i,partSize,chunksize):
        boundary = '----WebKitFormBoundarywiBIWjWR7osAkgFI'
        fid.seek((i-1)*chunksize)
        data_part = data.copy()
        data_part.update({
            "partSize": str(partSize),
            "partIndex": str(i),
            "file": (data["file"][0], fid.read(partSize), data["file"][1])
        })        
        with aiohttp.MultipartWriter('form-data',boundary) as writer:
            for key, value in data_part.items():
                if key != 'file':
                    part = writer.append(value)
                    part.set_content_disposition('form-data', name=key)
                else:
                    part = writer.append(value[1], {'Content-Type': value[2]})
                    part.set_content_disposition('form-data', name=key, filename=value[0])
            
            url = 'https://du.smartont.net:8443/openapi/client/upload2C'
            headers = {
                'Host': 'du.smartont.net:8443',
                'Origin': 'https://pan.wo.cn',
                'Referer': 'https://pan.wo.cn/',
                'Content-Type': 'multipart/form-data; boundary=----WebKitFormBoundarywiBIWjWR7osAkgFI',
                'Connection': 'keep-alive',
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
            }
            async with aiohttp.ClientSession(headers=headers) as session:
                async with session.post(url=url, data=writer, headers=headers) as response:
                    print(i, end='    ')
                    l = await response.text()
                    l = json.loads(l)
                    if l['code'] != '0000':
                        print(f'upload part error')
                    if 'fid' in l['data'].keys():
                        print('upload succeed')
            return []

def upload(filename, filetype, fileformat):
    chunksize = 4000000
    accesscode = '159b1050-e868-463f-9c3d-8bf4180c8067'
    batchNo = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
    filesize = os.path.getsize(filename)
    type_dict = {'image':"1","video":"2","audio":"3","doc":"4","other":"5"}
    params = {"spaceType":"0",
                "directoryId":"0",
                "batchNo":batchNo,
                "fileName":filename,
                "fileSize":filesize,
                "fileType":type_dict[filetype]}
    fileInfo = Wopan(accesscode).encrypt(str(params))
    if filesize < chunksize:
        totalPart = 1
        lastPart = filesize
    else:
        totalPart = math.floor(filesize / chunksize)
        lastPart = filesize - (totalPart-1)*chunksize
        data = {
            "uniqueId": str(filesize)+'-'+filename,
            "accessToken": accesscode,
            "fileName": filename,
            "psToken": "undefined",
            "fileSize": str(filesize),
            "totalPart": str(totalPart),
            "channel": "wocloud",
            "directoryId":"0",
            "fileInfo": fileInfo,
            "file": (filename, fileformat)
        }

    tasker = Tasker(nTask=5,tSleep=0.1)
    with open(filename,'rb') as f:
        tasker.run([uploadPart(f,data,1,chunksize,chunksize)])
        tasker.run([uploadPart(f,data,i,chunksize,chunksize) for i in range(2,totalPart)])
        tasker.run([uploadPart(f,data,totalPart,lastPart,chunksize)])

upload('hotel11.zip','other','text/plain')