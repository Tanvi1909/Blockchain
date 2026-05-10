// SPDX-License-Identifier: MIT
pragma solidity ^0.8.19;

contract Voting {

    struct Candidate {
        string name;
        uint256 voteCount;
    }

    Candidate[] public candidates;

    mapping(address => bool) public hasVoted;

    event VoteCasted(address voter, string candidateName);

    constructor() {
        candidates.push(Candidate("Tanvi", 0));
        candidates.push(Candidate("Suryansh", 0));
    }

    function vote(uint256 candidateIndex) public {

        require(!hasVoted[msg.sender], "Already voted");

        require(candidateIndex < candidates.length,
        "Invalid candidate");

        candidates[candidateIndex].voteCount++;

        hasVoted[msg.sender] = true;

        emit VoteCasted(
            msg.sender,
            candidates[candidateIndex].name
        );
    }

    function getVotes()
    public
    view
    returns(uint256,uint256)
    {
        return(
            candidates[0].voteCount,
            candidates[1].voteCount
        );
    }
}