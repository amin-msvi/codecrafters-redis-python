# Redis From Scratch (Python)
A fully functional Redis server implemented from scratch in Python 3.14, built as part of the [CodeCrafters](https://codecrafters.io/) Redis challenge.

Here are a couple of points I strictly tried to follow:
- I only used python's built-in libraries.
- I did my best to follow original Redis design decisions wherever was possible. For instance, the whole server is single-thread, so all the functionalities and architecutral decisions are complied with this limitation.
- 100% of the code is implemented by MYSELF not AI. I used AI to consult about design patterns, architectures, generating some diagrams, and original Redis internal logics. So AI was only involved as a consultant and visualization assistant.

## Architecture

```mermaid
graph TD
    subgraph Entry["Entry Point (main.py)"]
        CLI["CLI Argument Parsing"]
        DI["Dependency Wiring"]
    end

    subgraph Server["Server Layer"]
        RS["Single-thread RedisServer<br/>Event Loop + select()"]
        SR["ServerRole (ABC)<br/>Strategy Interface"]
        MR["MasterRole"]
        RR["ReplicaRole"]
        TS["TransactionState<br/>Interceptor"]
        PS["PubSubState<br/>Interceptor"]
    end

    subgraph Protocol["Protocol Layer"]
        RP["RESP Parser<br/>bytes → Python"]
        RE["RESP Encoder<br/>Python → bytes"]
        RB["RESPBuffer<br/>Byte Accumulation"]
    end

    subgraph Commands["Command Layer"]
        CR["CommandRegistry<br/>Auto-Discovery + Dispatch"]
        CMD["34 Command Implementations"]
    end

    subgraph Data["Data Layer"]
        SO["StringOps"]
        LO["ListOps"]
        STO["StreamOps"]
        ZO["ZSetOps"]
        GO["GeoOps"]
        DB["DataBase<br/>dict + TTL"]
    end

    subgraph Domain["Domain Objects"]
        SID["StreamID"]
        SE["StreamEntry"]
        ST["Stream"]
        ZS["ZSet"]
    end

    subgraph Persistence["Persistence Layer"]
        RDL["RDBLoader"]
        RDP["RDBParser"]
    end

    CLI --> DI
    DI --> RS
    RS --> SR
    SR --> MR
    SR --> RR
    RS --> TS
    RS --> PS
    RS --> RP
    RS --> RE
    RS --> CR
    CR --> CMD
    CMD --> SO
    CMD --> LO
    CMD --> STO
    CMD --> ZO
    CMD --> GO
    SO --> DB
    LO --> DB
    STO --> DB
    ZO --> DB
    GO --> ZO
    STO --> SID
    STO --> SE
    STO --> ST
    ZO --> ZS
    RDL --> RDP
    RDL --> DB

    style Entry fill:#e1f5fe
    style Server fill:#f3e5f5
    style Protocol fill:#fff3e0
    style Commands fill:#e8f5e9
    style Data fill:#fce4ec
    style Domain fill:#fff9c4
    style Persistence fill:#f1f8e9
```

**Key design decisions:**
- Single-threaded, non-blocking I/O via `select()` — no threads, no async/await
- **Strategy Pattern** for master/replica roles — zero conditionals in the server
- **Command Pattern** with auto-discovery + constructor-based DI
- **Interceptor Pattern** for transactions (MULTI/EXEC) and Pub/Sub
- **Callback + Closure** pattern for blocking commands (BLPOP, XREAD BLOCK)

## Features

| Category | Commands |
|---|---|
| Strings | `GET`, `SET` (EX/PX), `INCR` |
| Lists | `LPUSH`, `RPUSH`, `LPOP`, `LLEN`, `LRANGE`, `BLPOP` |
| Streams | `XADD`, `XRANGE`, `XREAD` (BLOCK) |
| Sorted Sets | `ZADD`, `ZCARD`, `ZRANGE`, `ZRANK`, `ZREM`, `ZSCORE` |
| Geo | `GEOADD`, `GEODIST`, `GEOPOS`, `GEOSEARCH` |
| Transactions | `MULTI`, `EXEC`, `DISCARD` |
| Pub/Sub | `SUBSCRIBE`, `UNSUBSCRIBE`, `PUBLISH` |
| Replication | `REPLCONF`, `PSYNC`, `WAIT` |
| ACL | `AUTH`, `ACL SETUSER/GETUSER` |
| General | `PING`, `ECHO`, `TYPE`, `KEYS`, `CONFIG`, `INFO` |
| Persistence | RDB file loading on startup |

## Running

Requires Python 3.14 and [uv](https://docs.astral.sh/uv/).

```bash
# Master on default port 6379
uv run -m app.main

# Custom port
uv run -m app.main --port 6380

# As replica
uv run -m app.main --port 6380 --replicaof "localhost 6379"

# With RDB persistence
uv run -m app.main --dir ./data --dbfilename dump.rdb
```

Connect with any Redis client:

```bash
redis-cli -p 6379
```
