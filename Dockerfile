FROM  ubuntu
WORKDIR /app

RUN apt-get update
RUN apt-get -y install python3-pip
RUN pip3 install --no-cache --upgrade pip setuptools

COPY requirements.txt ./
RUN pip3 install -r ./requirements.txt

COPY . ./
CMD [ "python3", "./listen.py" ]