# To start the backend, enter the following in two different terminals-

```
pip install -r requirements.txt
```

**backend**
```
uvicorn main:app --reload --host 0.0.0.0 --port 8001
```
**celery**
```
celery -A celery_app:celery_app worker --pool=threads --concurrency=4 --loglevel=info
```

### Run the above two commands from the ari-backend-main directory only


*You also need to build the redis image for celery*
```
docker run -d --name ari-redis -p 6379:6379 redis:7-alpine
```
*ensure to have docker desktop open in your laptop*
