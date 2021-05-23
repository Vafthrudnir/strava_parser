FROM python
WORKDIR /usr/src/app
COPY requirements.txt .

RUN pip install -r requirements.txt

RUN apt-get update && apt-get install -y dos2unix

COPY . .

RUN dos2unix ./host.sh

EXPOSE 5000

CMD ["./host.sh"]
