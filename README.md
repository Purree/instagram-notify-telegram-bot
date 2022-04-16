<h1>New instagram post notifier</h1>
This project send message to telegram then subscribed by user blogger post new photo.

<h2>How to install</h2>
1. Uninstall library with name "telegram" if you are not using venv, or you have this library. 
2. Run "pip install -r requirements.txt" in console.
3. Copy config.example.cfg file and delete "example" from its name.
4. In config.cfg write data as indicated there.
5. Run "python migration.py" in cmd.


<h3>If you use Docker</h3>
1. Copy config.example.cfg file and delete "example" from its name.
2. Copy .env.example file and delete "example" from its name.
3. In config.cfg and .env write data as indicated there.
4. Copy db data into ./database/mysql if you have it else skip this step.
5. Run `docker-compose up -d`.
6. *Do it if you skip 3 step* 
   1. Run `docker-compose exec notifier-app bash`.
   2. Run `python migration.py`.