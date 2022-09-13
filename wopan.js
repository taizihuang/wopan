function aes_encrypt(text) {
    var secretKey = $('.accesscode')[0].id;
    var iv = 'wNSOYIB1k1DjY5lA';
    var keyHex = CryptoJS.enc.Utf8.parse(secretKey.slice(0,16));
    var ivHex = CryptoJS.enc.Utf8.parse(iv);
    var encrypted = CryptoJS.AES.encrypt(text, keyHex, {
        "iv": ivHex,
        "mode": CryptoJS.mode.CBC,
        "padding": CryptoJS.pad.Pkcs7
    });
    return encrypted.toString();
}

function aes_decrypt(text) {
    var secretKey = $('.accesscode')[0].id;
    var iv = 'wNSOYIB1k1DjY5lA';
    var keyHex = CryptoJS.enc.Utf8.parse(secretKey.slice(0,16));
    var ivHex = CryptoJS.enc.Utf8.parse(iv);
    var decrypt = CryptoJS.AES.decrypt(text, keyHex, {
        "iv": ivHex,
        "mode": CryptoJS.mode.CBC,
        "padding": CryptoJS.pad.Pkcs7
    });
    return CryptoJS.enc.Utf8.stringify(decrypt);
}

function genHeader(key) {
    var channel = "wohome";
    var resTime = (new Date).getTime();
    var reqSeq = Math.floor(89999 * Math.random()) + 1e5;
    var version = "";
    var sign = md5(key+resTime+reqSeq+channel+version);
    return {"key":key,"resTime":resTime,"reqSeq":reqSeq,"channel":channel,"version":"","sign":sign}
}

function fetch(key, param_dict) {
    var secretKey = $('.accesscode')[0].id;
    var response = {};
    $.ajax({
        async: false,
        type: 'POST',
        url: 'https://panservice.mail.wo.cn/wohome/dispatcher',
        data: JSON.stringify({
            "header": genHeader(key), 
            "body":{
                "param": aes_encrypt(JSON.stringify(param_dict)),
                "secret":"true"}
        }),
        contentType: "application/json",
        dataType: 'json',
        headers: {
            "accesstoken": secretKey,
            "accept": "application/json",
        },
        success: function(jsonResponse) {
            var jsonData = JSON.parse(JSON.stringify(jsonResponse));
            response = JSON.parse(aes_decrypt(jsonData['RSP']['DATA']));
        }
    });
    return response
}

function fetchList(folder='0', dirID='0') {
    if (folder != '0') {
        dirID = fetchId(folder);
    };
    var param_dict = {"spaceType":"0","parentDirectoryId":dirID,"pageNum":0,"pageSize":100,"sortRule":0,"clientId":"1001000021"};
    var response = fetch('QueryAllFiles', param_dict);
    return response
}

function fetchId(folder) {
    if (folder == '0') {
        return '0'
    };
    var path = folder.split('/');
    var d = fetchList(folder='0');
    var name_dict = {};
    for (var i = 0; i < d['files'].length; i++) {
        name_dict[d['files'][i]['name']] = d['files'][i]['id'];
    };
    for (var i =0; i < path.length; i++) {
        if (! name_dict.hasOwnProperty(path[i])) {
            console.log('path does not exist');
            return '0'
        } else if (i < path.length - 1) {
            d = fetchList(undefined,dirID=name_dict[path[i]]);
            for (var j = 0; j < d['files'].length; j++) {
                name_dict[d['files'][j]['name']] = d['files'][j]['id'];
            };
        }
        else {
            return name_dict[path[i]]
        };
    };
}

function fetchURL(folder='0') {
    var dirID = fetchId(folder);
    var d = fetchList(undefined,dirID=dirID);
    var name_dict = {};
    var fidList = [];
    for (var i = 0; i < d['files'].length; i++) {
        name_dict[d['files'][i]['name']] = d['files'][i]['fid'];
        fidList[i] = d['files'][i]['fid'];
    };
    var param_dict = {"fidList": fidList, "clientId":"1001000001","spaceType":"0"};
    var url_list = fetch('GetDownloadUrl', param_dict);
    var fid_dict = {};
    for (var i = 0; i < url_list.length; i++) {
        fid_dict[url_list[i]['fid']] = url_list[i]['downloadUrl'];
    };
    var name_list = Object.keys(name_dict);
    var url_dict = {};
    for (var i = 0; i < name_list.length; i++) {
        var name = name_list[i]
        url_dict[name] = fid_dict[name_dict[name]];
    };
    return url_dict
}

function searchFile(filename, folder='0') {
    var url_dict = fetchURL(folder);
    var name_list = Object.keys(url_dict);
    var out_dict = {};
    for (i = 0; i < name_list.length; i++) {
        var name = name_list[i];
        if (name.includes(filename)) {
            out_dict[name] = url_dict[name]
        };
    };
    return out_dict
}

function fetchSrc(id, title, folder='0'){
    $('#'+id)[0].src = searchFile(id,folder)[title];
}