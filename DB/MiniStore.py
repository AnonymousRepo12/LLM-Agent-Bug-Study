import redis

class MiniStore:
    def __init__(self, host='localhost', port=6379, db=0):
        self.r = redis.Redis(host=host, port=port, db=db, decode_responses=True)

    def _make_key(self, framework, keyword):
        return f"{framework}_{keyword}"

    def save(self, framework, keyword, text):
        key = self._make_key(framework, keyword)
        if self.r.exists(key):
            return False  
        self.r.hset(key, mapping={
            "framework": framework,
            "keyword": keyword,
            "text": text
        })
        return True

    def get(self, framework, keyword):
        key = self._make_key(framework, keyword)
        data = self.r.hgetall(key)
        return data['text'] if data else None

    def exists(self, framework, keyword):
        key = self._make_key(framework, keyword)
        return self.r.exists(key) > 0

    def delete(self, framework, keyword):
        key = self._make_key(framework, keyword)
        return self.r.delete(key) > 0


