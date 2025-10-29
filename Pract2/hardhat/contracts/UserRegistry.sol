// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract UserRegistry {
    struct User {
        address addr;
        string username;
        uint256 createdAt;
        bool exists;
    }

    mapping(address => User) public users;
    event UserRegistered(address indexed userAddress, string username, uint256 createdAt);

    function register(string calldata username) external {
        require(!users[msg.sender].exists, "Already registered");
        users[msg.sender] = User({
            addr: msg.sender,
            username: username,
            createdAt: block.timestamp,
            exists: true
        });
        emit UserRegistered(msg.sender, username, block.timestamp);
    }

    function isRegistered(address addr) external view returns (bool) {
        return users[addr].exists;
    }
}
