## Help
```shell
python3 start.py -h
```

## Install 
```shell
sudo apt-get update
sudo apt-get -y install python3-pip mysql-client libmysqlclient-dev
pip3 install --no-cache --upgrade pip setuptools
```

## Example list of targets
```text
192.168.0.1:554
192.168.0.1:8554
192.168.0.1:80
192.168.0.2:554
```

## Run with MySql and do not save screenshots to DB (-ns)
```shell
python3 start.py -ns -ip ip.txt -du mysql://username:password@localhost:3306/bruter
```

## Run with Sqlite
```shell
python3 start.py -ip path/to/ip-port-list.txt 
```

## Restart broken or stopped brute
```shell
python3 start.py -ip path/to/ip-port-list.txt -id e908892f-0f22-4aca-95eb-21e35af28a3c
```

## Run using SOCKS5 proxy
```shell
python3 start.py -ip path/to/ip-port-list.txt -du mysql://username:password@localhost:3306/bruter -pr socks5://username:password@proxy.example.com:1080
```

## To test  queue
```shell
docker run --rm -it -p 15672:15672 -p 5672:5672 rabbitmq:3-management
```
```shell
docker run --network=host -e RABBITMQ_URL=amqp://guest:guest@192.168.1.2 -e QUEUE_NAME_TASK=rtsp_brute_task -e QUEUE_NAME_RESULT=rtsp_brute_result -it bruter
```