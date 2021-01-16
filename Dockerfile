# base image
FROM python

WORKDIR /usr/src/app

# Add logic to image
ADD / /usr/src/app

RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirement.txt

CMD [ "python", "./telegram_init.py" ]
