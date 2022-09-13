from Crypto.Cipher import AES
from requests_toolbelt  import MultipartEncoder
import hashlib,base64,json,math,random,time,re,requests,datetime,os

def clean(content):
    return re.sub(r'[\x00-\x10]',r'', content) 

class AESTool:
    def __init__(self, accesscode=''):
        self.key = 'XFmi9GS2hzk98jGX'.encode('utf-8')
        self.iv = 'wNSOYIB1k1DjY5lA'.encode('utf-8')
        self.accesscode = accesscode[:16].encode('utf-8')

    def pkcs7padding(self, text):
        """
        明文使用PKCS7填充
        """
        bs = 16
        length = len(text)
        bytes_length = len(text.encode('utf-8'))
        padding_size = length if (bytes_length == length) else bytes_length
        padding = bs - padding_size % bs
        padding_text = chr(padding) * padding
        self.coding = chr(padding)
        return text + padding_text

    def aes_encrypt(self, content, key):
        """
        AES加密
        """
        cipher = AES.new(key, AES.MODE_CBC, self.iv)
        # 处理明文
        content_padding = self.pkcs7padding(content)
        # 加密
        encrypt_bytes = cipher.encrypt(content_padding.encode('utf-8'))
        # 重新编码
        result = str(base64.b64encode(encrypt_bytes), encoding='utf-8')

        return result

    def aes_decrypt(self, content, key):
        """
        AES解密
        """
        cipher = AES.new(key, AES.MODE_CBC, self.iv)
        content = base64.b64decode(content)
        text = cipher.decrypt(content).decode('utf-8')
        return self.pkcs7padding(text)
    
    def login_encrypt(self):
        param = '{'+f'"phone":"13033062356","password":"#F4JTrHa5vVc","uuid":"","verifyCode":"","clientSecret":"{self.key.decode()}"'+'}'
        print(param)
        return self.aes_encrypt(str(param), self.key)

    def login_decrypt(self, content):
        return clean(self.aes_decrypt(content, self.key))

    def encrypt(self, content):
        return self.aes_encrypt(content, self.accesscode)

    def decrypt(self, content):
        return clean(self.aes_decrypt(content, self.accesscode))

def genHeader(key,channel):
    resTime = int(time.time()*1000)
    reqSeq = int(math.floor(89999 * random.random()) + 1e5)
    version = ''
    md5_object = hashlib.md5()
    md5_object.update(f'{key}{resTime}{reqSeq}{channel}{version}'.encode('utf8'))
    sign = md5_object.hexdigest()
    return {"key":key,"resTime":resTime,"reqSeq":reqSeq,"channel":channel,"version":"","sign":sign}

class Wopan():
    
    def __init__(self, accesscode):

        self.accesscode = accesscode
        self.url = 'https://panservice.mail.wo.cn/wohome/dispatcher'
        self.headers =  {
            'origin': 'https://pan.wo.cn',
            'referer': 'https://pan.wo.cn/',
            'accesstoken': accesscode,
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
        }

    def clean(content):
        return re.sub(r'[\x00-\x10]',r'', content) 

    def upload(self, filename, filetype, fileformat):
        #type_dict = {'image':"1","video":"2","audio":"3","doc":"4","other":"5"}

        chunksize = 4000000
        batchNo = datetime.datetime.today().strftime('%Y%m%d%H%M%S')
        filesize = os.path.getsize(filename)
        fileformat = 'text/plain'
        fileType = 'other'
        params = {"spaceType":"0",
                    "directoryId":"0",
                    "batchNo":batchNo,
                    "fileName":filename,
                    "fileSize":filesize,
                    "fileType":fileType}
        fileInfo = Wopan(self.accesscode).encrypt(str(params))
        if filesize < chunksize:
            totalPart = 1
            lastPart = filesize
        else:
            totalPart = math.floor(filesize / chunksize)
            lastPart = filesize - (totalPart-1)*chunksize

        with open(filename,'rb') as f:
            for i in range(1,totalPart+1):
                print(i, end="    ")
                if i != totalPart:
                    partSize = chunksize
                else:
                    partSize = lastPart
                data = {
                    "uniqueId": str(filesize)+'-'+filename,
                    "accessToken": self.accesscode,
                    "fileName": filename,
                    "psToken": "undefined",
                    "fileSize": str(filesize),
                    "totalPart": str(totalPart),
                    "partSize": str(partSize),
                    "partIndex": str(i),
                    "channel": "wocloud",
                    "directoryId":"0",
                    "fileInfo": fileInfo,
                    "file": (filename, f.read(partSize), fileformat)
                }
                m = MultipartEncoder(data)

                url = 'https://du.smartont.net:8443/openapi/client/upload2C'
                headers = {
                    'Host': 'du.smartont.net:8443',
                    'Origin': 'https://pan.wo.cn',
                    'Referer': 'https://pan.wo.cn/',
                    'Content-Type': m.content_type,
                    'Connection': 'keep-alive',
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/105.0.0.0 Safari/537.36'
                }
                l = json.loads(requests.post(url,headers=headers,data=m).content)
                if l['code'] != '0000':
                    print('upload error')
                    break
                if 'fid' in l['data'].keys():
                    print('upload succeed')

    def fetch(self, key, param_dict, channel='wohome'):

        aesTool = AESTool(self.accesscode)
        data = {
            "header": genHeader(key,channel), 
            "body":{
                "param": aesTool.encrypt(str(param_dict)),
                "secret":"true"}}
        response = json.loads(requests.post(self.url,data=str(data),headers=self.headers).content)
        if response['RSP']['RSP_CODE'] == '0000':
            return json.loads(self.decrypt(response['RSP']['DATA']))
        else:
            print('wrong accesscode')
            return {}

    def fetchList(self, folder='0', dirID='0'):
        if folder != '0':
            dirID = self.fetchId(folder)
        param_dict = {"spaceType":"0","parentDirectoryId":dirID,"pageNum":0,"pageSize":100,"sortRule":0,"clientId":"1001000021"}
        return self.fetch('QueryAllFiles', param_dict)

    def fetchId(self, folder):

        if folder == '0':
            return '0'

        path = folder.split('/')
        d = self.fetchList(dirID='0')
        if d == {}:
            return {}
        name_dict = {file['name']: file['id'] for file in d['files']}
        
        for i in range(len(path)):
            if path[i] not in name_dict.keys():
                print('path does not exist')
                return '0'
            elif i < len(path)-1:
                d = self.fetchList(dirID=name_dict[path[i]])
                name_dict = {file['name']: file['id'] for file in d['files']}
            else:
                return name_dict[path[i]]
    
    def fetchURL(self, folder='0'):
        dirID = self.fetchId(folder)
        d = self.fetchList(dirID=dirID)
        if d == {}:
            return {}
        name_dict = {file['name']: file['fid'] for file in d['files']}
        fidList = [file['fid'] for file in d['files']]

        param_dict = {"fidList": fidList, "clientId":"1001000001","spaceType":"0"}
        url_list = self.fetch('GetDownloadUrl', param_dict)
        fid_dict = {url['fid']: url['downloadUrl'] for url in url_list}

        return {name: fid_dict[name_dict[name]] for name in name_dict.keys()}

    def searchFile(self, filename, folder='0'):
        name_dict = self.fetchURL(folder)
        return {name: name_dict[name] for name in name_dict.keys() if filename in name}

    def decrypt(self, content):
        return AESTool(self.accesscode).decrypt(content)
    
    def encrypt(self, content):
        return AESTool(self.accesscode).encrypt(content)