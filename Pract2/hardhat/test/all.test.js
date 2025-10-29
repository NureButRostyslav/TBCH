const { expect } = require("chai");
const { ethers } = require("hardhat");

describe("Local contracts integration", function () {
  let userRegistry, dataStore, conditional;
  let owner, user1, user2;

  beforeEach(async function () {
    [owner, user1, user2] = await ethers.getSigners();
    const UR = await ethers.getContractFactory("UserRegistry");
    userRegistry = await UR.deploy();
    await userRegistry.waitForDeployment();

    const DS = await ethers.getContractFactory("DataStore");
    dataStore = await DS.deploy(userRegistry.target);
    await dataStore.waitForDeployment();

    const CE = await ethers.getContractFactory("ConditionalExecutor");
    conditional = await CE.deploy(ethers.parseEther("0.5")); // 0.5 ETH threshold
    await conditional.waitForDeployment();
  });

  it("should register users and prevent double registration", async function () {
    await userRegistry.connect(user1).register("alice");
    const u = await userRegistry.users(user1.address);
    expect(u.exists).to.equal(true);
    expect(u.username).to.equal("alice");

    await expect(userRegistry.connect(user1).register("alice2")).to.be.revertedWith("Already registered");
  });

  it("should allow registered user to save data", async function () {
    await userRegistry.connect(user1).register("bob");
    // if DataStore uses isRegistered
    // await expect(dataStore.connect(user1).save("my-data")).to.not.be.reverted;
    const tx = await dataStore.connect(user1).save("hello-ipfs-like");
    const receipt = await tx.wait();
    // event check
    const events = receipt.logs.map(l => dataStore.interface.parseLog(l)).filter(e => e && e.name === "ItemSaved");
    // simpler: fetch itemsOf
    const ids = await dataStore.getItemsOf(user1.address);
    expect(ids.length).to.equal(1);
    const item = await dataStore.getItem(ids[0]);
    expect(item.data).to.equal("hello-ipfs-like");
  });

  it("should execute conditional when threshold met", async function () {
    expect(await conditional.executed()).to.equal(false);
    // deposit less than threshold
    await user1.sendTransaction({ to: conditional.target, value: ethers.parseEther("0.1") });
    expect(await conditional.executed()).to.equal(false);
    // deposit enough
    await user2.sendTransaction({ to: conditional.target, value: ethers.parseEther("0.5") });
    expect(await conditional.executed()).to.equal(true);
  });
});