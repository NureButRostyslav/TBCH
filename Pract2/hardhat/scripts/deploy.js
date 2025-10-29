const fs = require("fs");
const path = require("path");
const hre = require("hardhat");

async function main() {
  const [deployer] = await hre.ethers.getSigners();
  console.log("Deploying contracts with account:", deployer.address);

  // Deploy UserRegistry
  const UserRegistry = await hre.ethers.getContractFactory("UserRegistry");
  const userRegistry = await UserRegistry.deploy();
  await userRegistry.waitForDeployment();
  console.log("UserRegistry deployed to:", userRegistry.target);

  // Deploy DataStore (constructor requires registry address)
  const DataStore = await hre.ethers.getContractFactory("DataStore");
  const dataStore = await DataStore.deploy(userRegistry.target);
  await dataStore.waitForDeployment();
  console.log("DataStore deployed to:", dataStore.target);

  // Deploy ConditionalExecutor with threshold 1 ether
  const ConditionalExecutor = await hre.ethers.getContractFactory("ConditionalExecutor");
  const conditional = await ConditionalExecutor.deploy(hre.ethers.parseEther("1.0"));
  await conditional.waitForDeployment();
  console.log("ConditionalExecutor deployed to:", conditional.target);

  // Save ABIs + addresses for Flask server consumption
  const outDir = path.join(__dirname, "..", "deployed");
  if (!fs.existsSync(outDir)) fs.mkdirSync(outDir);

  const save = (name, contract) => {
    const artifact = hre.artifacts.readArtifactSync(name);
    const data = {
      address: contract.target,
      abi: artifact.abi
    };
    fs.writeFileSync(path.join(outDir, `${name}.json`), JSON.stringify(data, null, 2));
  };

  save("UserRegistry", userRegistry);
  save("DataStore", dataStore);
  save("ConditionalExecutor", conditional);

  console.log("Deployment artifacts saved to ./deployed");
}

main()
  .then(() => process.exit(0))
  .catch((error) => {
    console.error(error);
    process.exit(1);
  });