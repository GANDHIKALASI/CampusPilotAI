"""
CampusPilot AI — Phase 3.4.5: Controlled Retrieval Evaluation Dataset.

Contains 30 realistic academic document chunks spanning 5 Computer Science subjects:
- Operating Systems (OS)
- Database Management Systems (DBMS)
- Computer Networks (CN)
- Computer Organization & Architecture (COA)
- Data Structures & Algorithms (DSA)

Includes 20 evaluation questions covering exact terminology, paraphrasing,
conceptual understanding, technical abbreviations, ambiguity, and negative/out-of-domain queries.
"""

from typing import Dict, List, Optional

# -----------------------------------------------------------------------------
# 30 ACADEMIC CHUNKS (6 per subject across 5 subjects)
# -----------------------------------------------------------------------------
EVAL_CHUNKS: List[Dict] = [
    # --- Operating Systems (OS) ---
    {
        "chunk_id": "os_chunk_01",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 42,
        "subject": "Operating Systems",
        "scope": "shared",
        "content": (
            "Round-robin CPU scheduling assigns a fixed time quantum (slice) to each active process in the "
            "ready queue. When the hardware timer interrupt fires, the operating system kernel invokes the "
            "scheduler, performs a context switch to save the current process control block (PCB), and moves "
            "the thread to the tail of the ready list. If the quantum is configured too short, CPU overhead "
            "from context switching dominates, whereas an overly large quantum degrades responsiveness to FCFS."
        ),
    },
    {
        "chunk_id": "os_chunk_02",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 88,
        "subject": "Operating Systems",
        "scope": "shared",
        "content": (
            "A context switch is the computational mechanism of saving the execution state of an active process "
            "or thread—including general-purpose registers, program counter (PC), and stack pointer—into its "
            "Process Control Block (PCB), and restoring the state of another thread. Context switches are pure "
            "overhead because no application work occurs during the transition, and they frequently invalidate CPU caches."
        ),
    },
    {
        "chunk_id": "os_chunk_03",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 154,
        "subject": "Operating Systems",
        "scope": "shared",
        "content": (
            "Deadlock in operating systems occurs when a set of concurrent processes are permanently blocked "
            "because each process holds a resource while awaiting another resource held by another process. "
            "The four Coffman conditions necessary for deadlock are Mutual Exclusion, Hold and Wait, No Preemption, "
            "and Circular Wait. Dijkstra's Banker's Algorithm dynamically avoids deadlock by simulating resource allocation "
            "to ensure the system never enters an unsafe state."
        ),
    },
    {
        "chunk_id": "os_chunk_04",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 210,
        "subject": "Operating Systems",
        "scope": "personal",
        "content": (
            "Virtual memory paging partitions the virtual address space into fixed-size blocks called pages, "
            "which map to physical memory frames via a page table. When a referenced page is absent from physical "
            "RAM, a page fault exception triggers the operating system to retrieve the page from secondary swap "
            "storage. Page replacement policies like Least Recently Used (LRU) and Second-Chance Clock select victim pages."
        ),
    },
    {
        "chunk_id": "os_chunk_05",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 275,
        "subject": "Operating Systems",
        "scope": "personal",
        "content": (
            "Process synchronization utilizes semaphores and mutexes to prevent race conditions in critical sections. "
            "A counting semaphore maintains an integer counter with atomic wait() (P) and signal() (V) operations. "
            "Binary semaphores act as locks. Classic synchronization benchmarks include the Producer-Consumer problem, "
            "the Readers-Writers problem, and the Dining Philosophers problem."
        ),
    },
    {
        "chunk_id": "os_chunk_06",
        "document_id": "doc_os_core",
        "filename": "Modern_Operating_Systems_Tanenbaum.pdf",
        "page_number": 340,
        "subject": "Operating Systems",
        "scope": "shared",
        "content": (
            "Unix file systems employ inode (index node) data structures to store file metadata, permissions, ownership, "
            "and data block pointers. An inode contains direct block pointers for small files, and single, double, "
            "and triple indirect block pointers for massive files. The directory entry simply maps a human-readable "
            "filename string to its corresponding inode number."
        ),
    },

    # --- Database Management Systems (DBMS) ---
    {
        "chunk_id": "db_chunk_01",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 35,
        "subject": "DBMS",
        "scope": "shared",
        "content": (
            "ACID properties govern relational transaction management. Atomicity ensures all transaction operations "
            "complete or none do (all-or-nothing). Consistency guarantees the database transitions from one valid state "
            "to another, satisfying integrity constraints. Isolation ensures concurrent transactions do not interfere, "
            "typically enforced via two-phase locking (2PL) or multi-version concurrency control (MVCC). Durability "
            "guarantees committed changes survive system crashes via write-ahead logging (WAL)."
        ),
    },
    {
        "chunk_id": "db_chunk_02",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 112,
        "subject": "DBMS",
        "scope": "shared",
        "content": (
            "B+ Tree indexes are balanced search trees widely used in database storage engines like PostgreSQL and InnoDB. "
            "Unlike standard B-trees, all user record keys and row pointers reside exclusively in leaf nodes, which are "
            "linked sequentially as a doubly linked list for fast range scans. Internal nodes store search routing keys. "
            "B+ Trees maintain O(log N) lookup, insertion, and deletion complexity while minimizing disk I/O operations."
        ),
    },
    {
        "chunk_id": "db_chunk_03",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 180,
        "subject": "DBMS",
        "scope": "shared",
        "content": (
            "Relational database normalization decomposes redundant tables to eliminate insertion, update, and deletion "
            "anomalies. First Normal Form (1NF) mandates atomic attribute values. Second Normal Form (2NF) eliminates partial "
            "functional dependencies on composite primary keys. Third Normal Form (3NF) removes transitive dependencies. "
            "Boyce-Codd Normal Form (BCNF) strictly requires that for every non-trivial functional dependency X -> Y, X must be a superkey."
        ),
    },
    {
        "chunk_id": "db_chunk_04",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 245,
        "subject": "DBMS",
        "scope": "personal",
        "content": (
            "Multi-Version Concurrency Control (MVCC) enables high-throughput concurrent database reads and writes. "
            "Under MVCC, write operations create new versions of tuple rows with transaction visibility timestamps (xmin/xmax), "
            "allowing read queries to inspect a consistent snapshot of the data without acquiring exclusive read locks. "
            "Readers never block writers, and writers never block readers."
        ),
    },
    {
        "chunk_id": "db_chunk_05",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 310,
        "subject": "DBMS",
        "scope": "personal",
        "content": (
            "Cost-based query optimization in SQL databases transforms declarative queries into efficient procedural execution "
            "plans. The query optimizer evaluates relational algebra equivalences, analyzes table statistics (cardinality, "
            "histograms), and selects physical join algorithms such as Nested Loop Join, Hash Join, or Sort-Merge Join."
        ),
    },
    {
        "chunk_id": "db_chunk_06",
        "document_id": "doc_db_systems",
        "filename": "Database_System_Concepts_Silberschatz.pdf",
        "page_number": 385,
        "subject": "DBMS",
        "scope": "shared",
        "content": (
            "The CAP theorem states that a distributed data store can simultaneously provide at most two of three guarantees: "
            "Consistency (every read receives the most recent write or an error), Availability (every non-failing node returns "
            "a response), and Partition Tolerance (the system sustains arbitrary network message drops). NoSQL databases "
            "typically choose AP (eventual consistency) or CP over traditional relational CA designs."
        ),
    },

    # --- Computer Networks (CN) ---
    {
        "chunk_id": "cn_chunk_01",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 58,
        "subject": "Computer Networks",
        "scope": "shared",
        "content": (
            "The Transmission Control Protocol (TCP) establishes reliable stream delivery using a three-way handshake: "
            "SYN, SYN-ACK, and ACK. TCP provides flow control using a sliding receive window (rwnd) to prevent sender "
            "buffer overflow, and congestion control algorithms like TCP Tahoe and Reno that modulate the congestion "
            "window (cwnd) through Slow Start, Congestion Avoidance, Fast Retransmit, and Fast Recovery."
        ),
    },
    {
        "chunk_id": "cn_chunk_02",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 120,
        "subject": "Computer Networks",
        "scope": "shared",
        "content": (
            "The Domain Name System (DNS) is a hierarchical distributed database resolving human-readable domain names "
            "into IP addresses. Resolution begins at root name servers, descends to Top-Level Domain (TLD) servers (.com, .edu), "
            "and finishes at authoritative DNS servers. DNS operates primarily over UDP port 53 for speed and supports "
            "record types including A (IPv4), AAAA (IPv6), CNAME (canonical alias), and MX (mail exchange)."
        ),
    },
    {
        "chunk_id": "cn_chunk_03",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 195,
        "subject": "Computer Networks",
        "scope": "shared",
        "content": (
            "Network layer routing protocols compute shortest path packet paths across autonomous systems. "
            "Link-state protocols like OSPF use Dijkstra's algorithm where each router floods complete topology link state. "
            "Distance-vector protocols like RIP use the distributed Bellman-Ford equation where routers exchange distance "
            "vectors with immediate neighbors, susceptible to the count-to-infinity problem solved by poison reverse."
        ),
    },
    {
        "chunk_id": "cn_chunk_04",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 260,
        "subject": "Computer Networks",
        "scope": "personal",
        "content": (
            "Classless Inter-Domain Routing (CIDR) replaced classful IP addressing by allowing variable-length subnet masks "
            "(VLSM). CIDR notation specifies network prefixes with a slash suffix (e.g., 192.168.1.0/24). Routers use "
            "the Longest Prefix Match (LPM) rule in their forwarding tables to route packets to the most specific matching destination route."
        ),
    },
    {
        "chunk_id": "cn_chunk_05",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 325,
        "subject": "Computer Networks",
        "scope": "personal",
        "content": (
            "HTTP/2 introduced binary framing, multiplexed streams over a single TCP connection, and header compression (HPACK) "
            "to eliminate head-of-line (HOL) blocking at the HTTP application layer. However, TCP-level HOL blocking still persisted. "
            "HTTP/3 completely replaces TCP with QUIC over UDP, offering zero-RTT connection resumption and independent stream delivery."
        ),
    },
    {
        "chunk_id": "cn_chunk_06",
        "document_id": "doc_cn_top_down",
        "filename": "Computer_Networking_Kurose_Ross.pdf",
        "page_number": 390,
        "subject": "Computer Networks",
        "scope": "shared",
        "content": (
            "The OSI 7-layer reference model comprises Physical, Data Link, Network, Transport, Session, Presentation, "
            "and Application layers. In contrast, the practical TCP/IP model condenses these into four architectural tiers: "
            "Link (Network Access), Internet (IP), Transport (TCP/UDP), and Application (HTTP, DNS, SMTP). Encapsulation appends "
            "headers at each descending protocol layer."
        ),
    },

    # --- Computer Organization & Architecture (COA) ---
    {
        "chunk_id": "coa_chunk_01",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 64,
        "subject": "Computer Organization",
        "scope": "shared",
        "content": (
            "Instruction pipelining in modern microprocessors divides instruction execution into multiple overlapped stages: "
            "Instruction Fetch (IF), Instruction Decode (ID), Execution (EX), Memory Access (MEM), and Write Back (WB). "
            "Pipelining hazards include Structural Hazards (hardware resource conflict), Data Hazards (RAW, WAR, WAW dependencies), "
            "and Control Hazards (conditional branch penalties mitigated by dynamic branch prediction)."
        ),
    },
    {
        "chunk_id": "coa_chunk_02",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 132,
        "subject": "Computer Organization",
        "scope": "shared",
        "content": (
            "A Translation Lookaside Buffer (TLB) is an on-chip associative hardware cache that stores recent virtual-to-physical "
            "page address translations. On a TLB hit, the CPU translates the memory address in a single clock cycle without "
            "querying the multi-level page table in main memory. A TLB miss forces a page table walk across memory hierarchies, "
            "incurring significant CPU latency."
        ),
    },
    {
        "chunk_id": "coa_chunk_03",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 204,
        "subject": "Computer Organization",
        "scope": "shared",
        "content": (
            "Cache memory leverages spatial and temporal locality to bridge CPU-memory speed disparities. "
            "Cache placement strategies include Direct-Mapped, N-Way Set-Associative, and Fully-Associative caches. "
            "Multiprocessor systems maintain cache coherence using snooping protocols such as MESI (Modified, Exclusive, "
            "Shared, Invalid) or directory-based schemes to avoid stale data reads across CPU cores."
        ),
    },
    {
        "chunk_id": "coa_chunk_04",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 278,
        "subject": "Computer Organization",
        "scope": "personal",
        "content": (
            "Direct Memory Access (DMA) enables high-speed peripheral I/O devices (e.g., NVMe controllers, network NICs) "
            "to transfer data directly to and from system RAM without routing bytes through the CPU ALU. The CPU initializes "
            "the DMA controller with source address, destination address, and byte count, after which the DMA controller "
            "steals bus cycles to complete the transfer and raises an interrupt upon completion."
        ),
    },
    {
        "chunk_id": "coa_chunk_05",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 344,
        "subject": "Computer Organization",
        "scope": "personal",
        "content": (
            "RISC (Reduced Instruction Set Computer) designs emphasize simple, fixed-length instructions executing in single clock "
            "cycles with load-store memory architectures (e.g., ARM, RISC-V). CISC (Complex Instruction Set Computer) designs "
            "(e.g., x86) provide rich, variable-length instructions capable of performing complex operations and direct memory manipulation."
        ),
    },
    {
        "chunk_id": "coa_chunk_06",
        "document_id": "doc_coa_hennessy",
        "filename": "Computer_Architecture_Patterson_Hennessy.pdf",
        "page_number": 412,
        "subject": "Computer Organization",
        "scope": "shared",
        "content": (
            "The IEEE 754 floating-point standard encodes real numbers into three bit fields: Sign bit (s), Biased Exponent (e), "
            "and Normalized Mantissa/Significand (m). Single-precision (32-bit) uses 1 sign bit, 8 exponent bits (bias 127), and 23 fraction bits. "
            "Double-precision (64-bit) uses 1 sign bit, 11 exponent bits (bias 1023), and 52 fraction bits, supporting representations of denormals, infinity, and NaN."
        ),
    },

    # --- Data Structures & Algorithms (DSA) ---
    {
        "chunk_id": "dsa_chunk_01",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 75,
        "subject": "Data Structures",
        "scope": "shared",
        "content": (
            "Red-Black Trees are self-balancing binary search trees ensuring O(log N) worst-case time complexity for search, "
            "insertion, and deletion. Each node stores a color bit (red or black). The tree preserves five invariant properties: "
            "the root is black, leaves (NIL) are black, red nodes cannot have red children (no two consecutive reds), and every path "
            "from a node to its descendant leaves contains the same black-height. Tree balance is restored via recoloring and tree rotations."
        ),
    },
    {
        "chunk_id": "dsa_chunk_02",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 140,
        "subject": "Data Structures",
        "scope": "shared",
        "content": (
            "Dijkstra's algorithm finds single-source shortest paths in weighted directed graphs with non-negative edge weights. "
            "Using a min-priority heap or Fibonacci heap, the algorithm iteratively extracts the vertex u with minimum distance, "
            "relaxing all outgoing edges (u, v). With a binary heap, Dijkstra runs in O((V + E) log V) time. If negative edge weights "
            "exist, the Bellman-Ford algorithm must be used instead to detect negative cycles."
        ),
    },
    {
        "chunk_id": "dsa_chunk_03",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 215,
        "subject": "Data Structures",
        "scope": "shared",
        "content": (
            "Hash tables implement associative arrays with O(1) average-case time complexity for lookups, insertions, and deletions. "
            "Collisions occur when distinct keys hash to the same bucket index. Separate Chaining resolves collisions using linked lists "
            "or balanced trees at each bucket. Open Addressing resolves collisions by probing within the table array using Linear Probing, "
            "Quadratic Probing, or Double Hashing. Table load factor alpha = n/m triggers dynamic resizing when it exceeds thresholds (e.g. 0.75)."
        ),
    },
    {
        "chunk_id": "dsa_chunk_04",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 288,
        "subject": "Data Structures",
        "scope": "personal",
        "content": (
            "Dynamic Programming (DP) solves complex optimization problems by breaking them down into overlapping subproblems "
            "exhibiting optimal substructure. Top-down DP uses recursion with memoization tables to cache subproblem results. "
            "Bottom-up DP iteratively fills a table starting from base cases. Canonical examples include the 0/1 Knapsack Problem, "
            "Longest Common Subsequence (LCS), Matrix Chain Multiplication, and Floyd-Warshall all-pairs shortest paths."
        ),
    },
    {
        "chunk_id": "dsa_chunk_05",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 360,
        "subject": "Data Structures",
        "scope": "personal",
        "content": (
            "Graph traversal algorithms explore vertices and edges systematically. Breadth-First Search (BFS) uses a FIFO queue "
            "to explore vertices level by level, finding unweighted shortest paths in O(V + E) time. Depth-First Search (DFS) uses "
            "recursion or an explicit LIFO stack to explore along branch paths until backtracking, classifying edges into tree, back, "
            "forward, and cross edges, useful for topological sorting and strongly connected components (Tarjan/Kosaraju)."
        ),
    },
    {
        "chunk_id": "dsa_chunk_06",
        "document_id": "doc_dsa_clrs",
        "filename": "Introduction_to_Algorithms_Cormen_Leiserson.pdf",
        "page_number": 435,
        "subject": "Data Structures",
        "scope": "shared",
        "content": (
            "Comparison-based sorting algorithms have a theoretical lower bound of Omega(N log N). QuickSort selects a pivot "
            "element and partitions the array into sub-arrays, achieving O(N log N) average time and O(N^2) worst-case time with O(log N) auxiliary stack space. "
            "MergeSort divides the array recursively and merges sorted halves, guaranteeing O(N log N) worst-case time but requiring O(N) auxiliary memory. "
            "HeapSort uses a binary max-heap to sort in-place with O(N log N) worst-case time."
        ),
    },
]


# -----------------------------------------------------------------------------
# 20 EVALUATION QUESTIONS WITH GROUND TRUTH RELEVANCE LABELS
# -----------------------------------------------------------------------------
EVAL_QUESTIONS: List[Dict] = [
    # Category 1: Exact Terminology Questions
    {
        "question_id": "q01_exact_acid",
        "query": "What are the ACID properties in database management systems?",
        "category": "exact_terminology",
        "subject": "DBMS",
        "expected_relevant_chunk_ids": ["db_chunk_01"],
    },
    {
        "question_id": "q02_exact_coffman",
        "query": "What are the four Coffman conditions required for operating system deadlock?",
        "category": "exact_terminology",
        "subject": "Operating Systems",
        "expected_relevant_chunk_ids": ["os_chunk_03"],
    },
    {
        "question_id": "q03_exact_dijkstra",
        "query": "How does Dijkstra's algorithm find shortest paths in a graph?",
        "category": "exact_terminology",
        "subject": "Data Structures",
        "expected_relevant_chunk_ids": ["dsa_chunk_02"],
    },

    # Category 2: Paraphrased Questions
    {
        "question_id": "q04_para_context_switch",
        "query": "How does a computer switch between running different programs or threads?",
        "category": "paraphrased",
        "subject": "Operating Systems",
        "expected_relevant_chunk_ids": ["os_chunk_02", "os_chunk_01"],
    },
    {
        "question_id": "q05_para_bplus_tree",
        "query": "Why do relational database storage engines use multi-way balanced index trees for range queries?",
        "category": "paraphrased",
        "subject": "DBMS",
        "expected_relevant_chunk_ids": ["db_chunk_02"],
    },
    {
        "question_id": "q06_para_virtual_memory",
        "query": "What happens when an application requests memory that is not currently loaded in physical RAM?",
        "category": "paraphrased",
        "subject": "Operating Systems",
        "expected_relevant_chunk_ids": ["os_chunk_04"],
    },

    # Category 3: Conceptual Questions
    {
        "question_id": "q07_concept_normalization",
        "query": "Why is database normalization important and how does BCNF prevent anomalies?",
        "category": "conceptual",
        "subject": "DBMS",
        "expected_relevant_chunk_ids": ["db_chunk_03"],
    },
    {
        "question_id": "q08_concept_tcp_reliability",
        "query": "Explain how TCP guarantees reliable stream delivery and handles network congestion.",
        "category": "conceptual",
        "subject": "Computer Networks",
        "expected_relevant_chunk_ids": ["cn_chunk_01"],
    },
    {
        "question_id": "q09_concept_pipelining",
        "query": "How does instruction pipelining increase CPU throughput and what causes pipeline stalls?",
        "category": "conceptual",
        "subject": "Computer Organization",
        "expected_relevant_chunk_ids": ["coa_chunk_01"],
    },

    # Category 4: Related Context Questions
    {
        "question_id": "q10_related_dns_ip",
        "query": "How are human-friendly web domain names converted into numerical network addresses?",
        "category": "related_context",
        "subject": "Computer Networks",
        "expected_relevant_chunk_ids": ["cn_chunk_02"],
    },
    {
        "question_id": "q11_related_sorting_bounds",
        "query": "Compare QuickSort and MergeSort time complexity and memory usage.",
        "category": "related_context",
        "subject": "Data Structures",
        "expected_relevant_chunk_ids": ["dsa_chunk_06"],
    },
    {
        "question_id": "q12_related_dma_io",
        "query": "How do hardware peripherals transfer data to main memory without continuous CPU intervention?",
        "category": "related_context",
        "subject": "Computer Organization",
        "expected_relevant_chunk_ids": ["coa_chunk_04"],
    },

    # Category 5: Ambiguous Questions
    {
        "question_id": "q13_ambig_pipeline",
        "query": "What is a pipeline and how does it execute tasks?",
        "category": "ambiguous",
        "subject": "Computer Organization",
        "expected_relevant_chunk_ids": ["coa_chunk_01"],
    },
    {
        "question_id": "q14_ambig_consistency",
        "query": "Explain consistency models in distributed data systems.",
        "category": "ambiguous",
        "subject": "DBMS",
        "expected_relevant_chunk_ids": ["db_chunk_06", "db_chunk_01"],
    },

    # Category 6: Out-of-Domain / Negative Control Questions (Unanswerable)
    {
        "question_id": "q15_neg_crispr",
        "query": "How does CRISPR Cas9 guide RNA perform targeted gene editing in cellular genomes?",
        "category": "unanswerable_negative",
        "subject": "Biology",
        "expected_relevant_chunk_ids": [],  # Empty ground truth: should retrieve 0 chunks at calibrated threshold
    },
    {
        "question_id": "q16_neg_plate_tectonics",
        "query": "What causes continental drift and seismic subduction zones in planetary geology?",
        "category": "unanswerable_negative",
        "subject": "Geology",
        "expected_relevant_chunk_ids": [],
    },
    {
        "question_id": "q17_neg_organic_chemistry",
        "query": "Explain the Fischer esterification reaction mechanism between carboxylic acids and alcohols.",
        "category": "unanswerable_negative",
        "subject": "Chemistry",
        "expected_relevant_chunk_ids": [],
    },

    # Category 7: Technical Abbreviations & Jargon Questions
    {
        "question_id": "q18_abbrev_tlb",
        "query": "What is the function of a TLB and how does a TLB miss impact memory latency?",
        "category": "technical_abbreviation",
        "subject": "Computer Organization",
        "expected_relevant_chunk_ids": ["coa_chunk_02"],
    },
    {
        "question_id": "q19_abbrev_cidr",
        "query": "How does CIDR with VLSM and longest prefix match work in IP routing?",
        "category": "technical_abbreviation",
        "subject": "Computer Networks",
        "expected_relevant_chunk_ids": ["cn_chunk_04"],
    },
    {
        "question_id": "q20_abbrev_rbt_avl",
        "query": "What are the invariant properties of Red-Black Trees (RBT)?",
        "category": "technical_abbreviation",
        "subject": "Data Structures",
        "expected_relevant_chunk_ids": ["dsa_chunk_01"],
    },
]
