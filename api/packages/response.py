class Response:
  @staticmethod
  def parsejson(msg, response, status):
        data = {}
        temp = ""
        data["error"] = 0
        data["code"] = 0
        data["data"] = {}
        data["msg"] = msg     
        if status == 200:
            data['code'] = 0
        elif status == 201:
            data['code'] = 1
            data['data'] = response
        elif status == 202:
            data['code'] = 2
            data['data'] = response          
        elif status == 400:
            temp_list = []
            for key,item in msg.items():
                temp_list.append(key.title() +' : ' + item[0])
            data["error"] = 1
            data["msg"] = ', '.join(temp_list)          
        elif status == 403:
            data["error"] = 1
            data["msg"] = msg
            data['code'] = 3
        elif status == 404:
            data['error'] = 1

        return data

  @staticmethod
  def getdocs():
    _response_docs = {
                        400 :   'List of Error Messages',
                        201 :   'Not Set'

                    }
    return _response_docs