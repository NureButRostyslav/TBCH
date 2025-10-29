Installation guide:
1. Setup blockchain:

cd hardhat
npm install    // once
npx hardhat node

Leave this console be

2. Compile contracts (in different console)

cd hardhat
npx hardhat run scripts/deploy.js --network localhost


3. run tests 

npm run test


4. Setup virtual environment:

cd ../flask_server
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt   // once


If venv\Scripts\activate fails, do 
	
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass 	
.\venv\Scripts\activate
pip install -r requirements.txt   // once


5. Copy files from hardhat/deployed to flusk_server/contract_info

6. Launch server, wait untill the server is ready

python server.py


7. Open client/index.html in a browser
