// SPDX-License-Identifier: MIT
pragma solidity ^0.8.18;

contract ConditionalExecutor {
    uint256 public threshold;
    address public owner;
    bool public executed;

    event ConditionMet(address indexed who, uint256 amount, uint256 time);
    event ThresholdUpdated(uint256 oldValue, uint256 newValue);

    constructor(uint256 _threshold) {
        threshold = _threshold;
        owner = msg.sender;
        executed = false;
    }

    // Fallback to accept ETH and trigger condition
    receive() external payable {
        require(!executed, "Already executed");
        if (msg.value >= threshold) {
            executed = true;
            emit ConditionMet(msg.sender, msg.value, block.timestamp);
        }
    }

    function setThreshold(uint256 newThreshold) external {
        require(msg.sender == owner, "Only owner");
        emit ThresholdUpdated(threshold, newThreshold);
        threshold = newThreshold;
    }
}