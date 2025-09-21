from blockchain import Blockchain

# readonly blocks

if __name__ == "__main__":
    my_blockchain = Blockchain(readonly=True)

    # Додаємо кілька блоків
    my_blockchain.add_block({
        "tx_type": "UPLOAD",
        "file_id": "uuid-123",
        "file_hash": "sha256:abc123",
        "owner": "alice",
        "timestamp": 1694612096,
        "source": {
            "storage_type": "LOCAL",
            "location": "/local/path/photo.jpg"
        },
        "destination": {
            "storage_type": "HDD",
            "location": "server_2:/mnt/hdd1/partition3",
            "cid": "QmManifestCID"
        },
        "version": 1,
        "metadata": {"file_name": "photo.jpg", "size": 523000, "format": "jpg"},
        "signature": "0xdeadbeef"
    })

    my_blockchain.add_block({
        "tx_type": "MOVE",
        "file_id": "uuid-123",
        "file_hash": "sha256:abc123",
        "owner": "system",
        "timestamp": 1694613096,
        "source": {
            "storage_type": "HDD",
            "location": "server_2:/mnt/hdd1/partition3",
            "cid": "QmManifestCID"
        },
        "destination": {
            "storage_type": "SSD",
            "location": "server_5:/mnt/ssd1",
            "cid": "QmManifestCID"
        },
        "version": 1,
        "metadata": {"file_name": "photo.jpg", "size": 523000, "format": "jpg"},
        "signature": "0xsystem-signature"
    })

    my_blockchain.add_block({
        "tx_type": "UPLOAD",
        "file_id": "uuid-123",
        "file_hash": "sha256:prgts",
        "owner": "alice",
        "timestamp": 1694615196,
        "source": {
            "storage_type": "LOCAL",
            "location": "/local/path/photo2.jpg"
        },
        "destination": {
            "storage_type": "HDD",
            "location": "server_2:/mnt/hdd1/partition3",
            "cid": "QmManifestCID"
        },
        "version": 1,
        "metadata": {"file_name": "photo.jpg", "size": 523000, "format": "jpg"},
        "signature": "0xdeadbeef"
    })

    print("\nCurrent blockchain:")
    my_blockchain.print_chain()

    print("\nValidity check:")
    if my_blockchain.is_chain_valid():
        print("Blockchain is valid")
    else:
        print("Blockchain is invalid")

    # Імітація зміни даних
    print("\nEditing blockchain block data...")
    my_blockchain.chain[3].data = {
        "tx_type": "UPLOAD",
        "file_id": "uuid-123",
        "file_hash": "sha256:prgts",
        "owner": "tom",
        "timestamp": 1694615196,
        "source": {
            "storage_type": "LOCAL",
            "location": "/local/path/photo3.jpg"
        },
        "destination": {
            "storage_type": "HDD",
            "location": "server_2:/mnt/hdd1/partition3",
            "cid": "QmManifestCID"
        },
        "version": 1,
        "metadata": {"file_name": "photo.jpg", "size": 523000, "format": "jpg"},
        "signature": "0xdeadbeef"
    }

    print("\nValidity check after edit attempt:")
    if my_blockchain.is_chain_valid():
        print("Blockchain is valid")
    else:
        print("Blockchain is invalid")

    print("\nAdding a new block after an edit attempt:")
    my_blockchain.add_block({
        "tx_type": "UPLOAD",
        "file_id": "uuid-123",
        "file_hash": "sha256:prgts",
        "owner": "alice",
        "timestamp": 1694617196,
        "source": {
            "storage_type": "LOCAL",
            "location": "/local/path/photo000.jpg"
        },
        "destination": {
            "storage_type": "HDD",
            "location": "server_2:/mnt/hdd1/partition3",
            "cid": "QmManifestCID"
        },
        "version": 1,
        "metadata": {"file_name": "photo.jpg", "size": 523000, "format": "jpg"},
        "signature": "0xdeadbeef"
    })