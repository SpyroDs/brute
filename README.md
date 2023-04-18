## Help
```shell
python3 start.py -h
```
## List of targets example
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
python3 start.py -ip ip.txt 
```

## Restart broken or stopped brute
```shell
python3 start.py -ip ip.txt -id e908892f-0f22-4aca-95eb-21e35af28a3c
```

## Run using SOCKS5 proxy
```shell
python3 start.py -ip ip.txt -du mysql://username:password@localhost:3306/bruter -pr socks5://username:password@proxy.example.com:1080
```
