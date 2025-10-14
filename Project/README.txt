Installation guide:
1. Setup virtual environment:

python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt


If venv\Scripts\activate fails, do 
	
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 	
.\venv\Scripts\activate
pip install -r requirements.txt



2. Launch server

python server.py



3. Wait until the server is ready. Will take a lot of time on first launch.



4. In another terminal launch client

python client.py
