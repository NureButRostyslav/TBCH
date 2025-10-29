// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

import "./UserRegistry.sol";

contract DataStore {
    struct Item {
        uint256 id;
        address owner;
        string data;
        uint256 createdAt;
    }

    UserRegistry public registry;
    uint256 public nextId = 1;
    mapping(uint256 => Item) public items;
    mapping(address => uint256[]) public itemsOf;

    event ItemSaved(uint256 indexed id, address indexed owner, string data, uint256 createdAt);

    constructor(address registryAddress) {
        registry = UserRegistry(registryAddress);
    }

    function save(string calldata data) external returns (uint256) {
        // only registered users
        require(registry.isRegistered(msg.sender), "Not a registered user");

        uint256 id = nextId++;
        items[id] = Item({
            id: id,
            owner: msg.sender,
            data: data,
            createdAt: block.timestamp
        });
        itemsOf[msg.sender].push(id);
        emit ItemSaved(id, msg.sender, data, block.timestamp);
        return id;
    }

    function getItem(uint256 id) external view returns (Item memory) {
        return items[id];
    }

    function getItemsOf(address owner) external view returns (uint256[] memory) {
        return itemsOf[owner];
    }
}
