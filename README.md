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

## Run with MySql
```shell
python3 start.py -ip ip.txt -du mysql://username:password@localhost:3306/bruter
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

## Full arguments list

```text
optional arguments:
  -h, --help                            show this help message and exit
  -t, --targets TARGETS                 the targets on which to scan for open RTSP streams
  -ip, --targets-ip-port TARGETS_IP_PORT
                                        IP and port targets, separated by :
  -du, --db-url DB_URL                  Database url
  -id, --brute-id BRUTE_ID              Brute id to finish stopped or broken brute
  -pr, --proxy PROXY                    Proxy url i.e. socks5://user:password@192.168.0.1:2000
  -p, --ports PORTS [PORTS ...]         the ports on which to search for RTSP streams
  -r, --routes ROUTES                   the path on which to load a custom routes
  -c, --credentials CREDENTIALS         the path on which to load a custom credentials
  -ct, --check-threads N                the number of threads to brute-force the routes
  -bt, --brute-threads N                the number of threads to brute-force the credentials
  -st, --screenshot-threads N           the number of threads to screenshot the streams
  -T, --timeout TIMEOUT                 the timeout to use for sockets
  -d, --debug                           enable the debug logs
```