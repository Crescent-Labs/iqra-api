# Iqra api

Iqra is a tool meant to allow Muslims to search the Quran using speech recognition. This repo contains the code for the Iqra api. There are also repos for the [website](https://github.com/Crescent-Labs/iqra-web), [Android client](https://github.com/Crescent-Labs/iqra-android), and [iOS client](https://github.com/Crescent-Labs/iqra-ios).

### Setup

First install dependencies:
```
pip install -r .\requirements.txt
```

Then setup sqlite and load its contents:
```
python dbCreate.py
python dbMigrate.py
python seed.py
```

Finally, run the flask server:
```
python app.py
```

You can then make requests to `http://127.0.0.1:5000`.

A python example request is included in `exampleRequest.py`.

### Contributing

We actively welcome pull requests!

### License

The Iqra api is available under the GNU GPLv3 license. See the LICENSE file for more info.
