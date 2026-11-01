"""
Canonical academic curriculum structure for BCA Semester V and Semester VI.

Acts as the single source of truth grounded in the official BCA syllabus:
- Semester V:
    1. Software Engineering (Core XI) - Units I-IV
    2. Introduction to Artificial Intelligence (Core XII (A)) - Units I-IV
    3. Introduction to Data Science (Core XII (B)) - Units I-IV
    4. Programming in Java (Major XIII) - Units I-IV
    5. Java Programming Lab (BCA 6.1 Lab) - 21 Practical Exercises
- Semester VI:
    1. Algorithm Design Techniques (Core XIV) - Units I-IV
    2. Algorithm Design Lab (BCA 6.2 Lab) - 12 Practical Exercises
    3. Project Work-I (Core XV / BCA 6.3) - 14 Report Sections & 5 Evaluation Criteria
"""

from typing import Any, Dict, List

# Deterministic UUIDs matching database migration 006
SEM_5_ID = "55555555-5555-5555-5555-555555555555"
SEM_6_ID = "66666666-6666-6666-6666-666666666666"

SEMESTER_5_SUBJECTS: List[Dict[str, Any]] = [
    {
        "id": "50000001-0000-0000-0000-000000000001",
        "semester_id": SEM_5_ID,
        "name": "Software Engineering",
        "code": "Core XI",
        "subject_type": "theory",
        "order_index": 1,
        "description": "Fundamental software engineering principles, lifecycle models, estimation techniques, system analysis, design paradigms, testing methodologies, and maintenance.",
        "units": [
            {
                "id": "50000011-0000-0000-0000-000000000001",
                "subject_id": "50000001-0000-0000-0000-000000000001",
                "unit_number": 1,
                "title": "Introduction to Software Engineering & Lifecycle Models",
                "topics": "Introduction, evolution of software engineering, software development projects, software lifecycle models, Waterfall, RAD, Agile and Spiral models.",
                "order_index": 1,
            },
            {
                "id": "50000011-0000-0000-0000-000000000002",
                "subject_id": "50000001-0000-0000-0000-000000000001",
                "unit_number": 2,
                "title": "Software Project Management & Estimation",
                "topics": "Software Project Management, project planning, estimation techniques, COCOMO, Halstead's Software Science, scheduling, staffing, risk management and configuration management.",
                "order_index": 2,
            },
            {
                "id": "50000011-0000-0000-0000-000000000003",
                "subject_id": "50000001-0000-0000-0000-000000000001",
                "unit_number": 3,
                "title": "Requirement Analysis, Specification & Design",
                "topics": "Requirement Analysis and Specification, SRS, formal specification, software design, cohesion, coupling, function-oriented and object-oriented design.",
                "order_index": 3,
            },
            {
                "id": "50000011-0000-0000-0000-000000000004",
                "subject_id": "50000001-0000-0000-0000-000000000001",
                "unit_number": 4,
                "title": "Coding, Testing, Verification & Maintenance",
                "topics": "Coding, code review, software documentation, testing, unit testing, black-box testing, white-box testing, debugging, integration testing, system testing and software maintenance.",
                "order_index": 4,
            },
        ],
        "practicals": [],
    },
    {
        "id": "50000002-0000-0000-0000-000000000002",
        "semester_id": SEM_5_ID,
        "name": "Introduction to Artificial Intelligence",
        "code": "Core XII (A)",
        "subject_type": "theory",
        "order_index": 2,
        "description": "Foundations of AI, state-space search heuristics, logic representation, inference engines, NLP pipelines, and classical expert systems. Note: In the official university syllabus, AI is elective option (A) under Core XII alongside Data Science (B); CampusPilot provides both as distinct full subjects.",
        "units": [
            {
                "id": "50000012-0000-0000-0000-000000000001",
                "subject_id": "50000002-0000-0000-0000-000000000002",
                "unit_number": 1,
                "title": "Introduction to AI & Uninformed Search",
                "topics": "Introduction to AI, scope, characteristics of AI problems, Turing Test, intelligent agents, state-space search, production systems, BFS, DFS, iterative deepening, bidirectional search and beam search.",
                "order_index": 1,
            },
            {
                "id": "50000012-0000-0000-0000-000000000002",
                "subject_id": "50000002-0000-0000-0000-000000000002",
                "unit_number": 2,
                "title": "Informed Heuristic Search & Constraint Satisfaction",
                "topics": "Informed search, heuristic search, hill climbing, best-first search, A* algorithm, problem reduction, AO*, constraint satisfaction and means-end analysis.",
                "order_index": 2,
            },
            {
                "id": "50000012-0000-0000-0000-000000000003",
                "subject_id": "50000002-0000-0000-0000-000000000002",
                "unit_number": 3,
                "title": "Knowledge Representation & Reasoning Under Uncertainty",
                "topics": "Knowledge representation, propositional logic, predicate logic, resolution, unification, forward and backward chaining, semantic nets, frames, scripts and reasoning under uncertainty.",
                "order_index": 3,
            },
            {
                "id": "50000012-0000-0000-0000-000000000004",
                "subject_id": "50000002-0000-0000-0000-000000000002",
                "unit_number": 4,
                "title": "Natural Language Processing & Expert Systems",
                "topics": "Natural Language Processing, language understanding, parsing, transition networks and expert systems, including MYCIN and DENDRAL.",
                "order_index": 4,
            },
        ],
        "practicals": [],
    },
    {
        "id": "50000003-0000-0000-0000-000000000003",
        "semester_id": SEM_5_ID,
        "name": "Introduction to Data Science",
        "code": "Core XII (B)",
        "subject_type": "theory",
        "order_index": 3,
        "description": "Essential data science methodologies, R language programming, tidy data wrangling, APIs, and multivariate exploratory data analysis. Note: In the official university syllabus, Data Science is elective option (B) under Core XII alongside AI (A); CampusPilot provides both as distinct full subjects.",
        "units": [
            {
                "id": "50000013-0000-0000-0000-000000000001",
                "subject_id": "50000003-0000-0000-0000-000000000003",
                "unit_number": 1,
                "title": "Data Scientist's Toolbox & Environment",
                "topics": "Data Scientist's Toolbox, turning data into actionable knowledge, version control, Markdown, Git, GitHub, R and RStudio.",
                "order_index": 1,
            },
            {
                "id": "50000013-0000-0000-0000-000000000002",
                "subject_id": "50000003-0000-0000-0000-000000000003",
                "unit_number": 2,
                "title": "R Programming Foundations & Data Structures",
                "topics": "R programming basics, data types, objects, reading and writing data, control structures, functions, scope rules, dates and times, loop functions, debugging, simulation and code profiling.",
                "order_index": 2,
            },
            {
                "id": "50000013-0000-0000-0000-000000000003",
                "subject_id": "50000003-0000-0000-0000-000000000003",
                "unit_number": 3,
                "title": "Getting, Wrangling & Cleaning Data",
                "topics": "Getting and Cleaning Data, obtaining data from web, APIs and databases, different data formats, data cleaning and tidy data.",
                "order_index": 3,
            },
            {
                "id": "50000013-0000-0000-0000-000000000004",
                "subject_id": "50000003-0000-0000-0000-000000000004",
                "unit_number": 4,
                "title": "Exploratory Data Analysis & Multivariate Visualization",
                "topics": "Exploratory Data Analysis, summarizing data, hypothesis exploration and multivariate statistical techniques for visualizing high-dimensional data.",
                "order_index": 4,
            },
        ],
        "practicals": [],
    },
    {
        "id": "50000004-0000-0000-0000-000000000004",
        "semester_id": SEM_5_ID,
        "name": "Programming in Java",
        "code": "Major XIII",
        "subject_type": "theory",
        "order_index": 4,
        "description": "Object-oriented software development using Java, package design, multithreaded concurrency, streams, networking, and JDBC database access.",
        "units": [
            {
                "id": "50000014-0000-0000-0000-000000000001",
                "subject_id": "50000004-0000-0000-0000-000000000004",
                "unit_number": 1,
                "title": "Java Fundamentals & Language Constructs",
                "topics": "Java history, architecture, features, syntax, variables, data types, operators, decision-making, loops, methods and keyboard input.",
                "order_index": 1,
            },
            {
                "id": "50000014-0000-0000-0000-000000000002",
                "subject_id": "50000004-0000-0000-0000-000000000004",
                "unit_number": 2,
                "title": "Object-Oriented Programming, Inheritance & Packages",
                "topics": "OOP concepts, classes, objects, constructors, inheritance, interfaces, polymorphism, overloading, overriding, packages and garbage collection.",
                "order_index": 2,
            },
            {
                "id": "50000014-0000-0000-0000-000000000003",
                "subject_id": "50000004-0000-0000-0000-000000000004",
                "unit_number": 3,
                "title": "Arrays, Strings, Streams & Java I/O",
                "topics": "Arrays, strings, StringBuffer, StringBuilder, Java I/O, streams, file handling and compression.",
                "order_index": 3,
            },
            {
                "id": "50000014-0000-0000-0000-000000000004",
                "subject_id": "50000004-0000-0000-0000-000000000004",
                "unit_number": 4,
                "title": "Exceptions, Multithreading, Sockets & JDBC",
                "topics": "Exception handling, multithreading, synchronization, networking, TCP/IP and JDBC.",
                "order_index": 4,
            },
        ],
        "practicals": [],
    },
    {
        "id": "50000005-0000-0000-0000-000000000005",
        "semester_id": SEM_5_ID,
        "name": "Java Programming Lab",
        "code": "BCA 6.1 Lab",
        "subject_type": "practical",
        "order_index": 5,
        "description": "Comprehensive practical laboratory course covering all 21 Java programming assignments from language fundamentals to JDBC and network socket programming.",
        "units": [],
        "practicals": [
            {"id": "50000021-0000-0000-0000-000000000001", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 1, "title": "Sum of Command Line Integers", "description": "To find the sum of any number of integers entered as command line arguments.", "order_index": 1},
            {"id": "50000021-0000-0000-0000-000000000002", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 2, "title": "Factorial of Given Number", "description": "To find the factorial of a given number.", "order_index": 2},
            {"id": "50000021-0000-0000-0000-000000000003", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 3, "title": "Decimal to Binary Conversion", "description": "To convert a decimal to binary number.", "order_index": 3},
            {"id": "50000021-0000-0000-0000-000000000004", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 4, "title": "Prime Number Verification", "description": "To check if a number is prime or not, by taking the number as input from the keyboard.", "order_index": 4},
            {"id": "50000021-0000-0000-0000-000000000005", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 5, "title": "Interactive Sum of Integers", "description": "To find the sum of any number of integers interactively, i.e., entering every number from the keyboard, whereas the total number of integers is given as a command line argument.", "order_index": 5},
            {"id": "50000021-0000-0000-0000-000000000006", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 6, "title": "String and StringBuffer Functions", "description": "Write a program that show working of different functions of String and StringBufferclasss like setCharAt( ), setLength( ), append( ), insert( ), concat( )and equals( ).", "order_index": 6},
            {"id": "50000021-0000-0000-0000-000000000007", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 7, "title": "Distance Class & This Pointer", "description": "Write a program to create a – “distance” class with methods where distance is computed in terms of feet and inches, how to create objects of a class and to see the use of this pointer", "order_index": 7},
            {"id": "50000021-0000-0000-0000-000000000008", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 8, "title": "Distance Constructor & Object Cloning", "description": "Modify the – “distance” class by creating constructor for assigning values (feetandinches) to the distance object. Create another object and assign second object as reference variable to another object reference variable. Further create a third object which is a clone of the first object.", "order_index": 8},
            {"id": "50000021-0000-0000-0000-000000000009", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 9, "title": "Overloading & Automatic Type Conversion", "description": "Write a program to show that during function overloading, if no matching argument is found, then Java will apply automatic type conversions (from lower to higher data type).", "order_index": 9},
            {"id": "50000021-0000-0000-0000-000000000010", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 10, "title": "Access Specifiers & Pass-by-Value/Reference", "description": "Write a program to show the difference between public and private access specifiers. The program should also show that primitive data types are passed by value and objects are passed by reference and to learn use of final keyword.", "order_index": 10},
            {"id": "50000021-0000-0000-0000-000000000011", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 11, "title": "Static Functions & Varargs", "description": "Write a program to show the use of static functions and to pass variable length arguments in a function.", "order_index": 11},
            {"id": "50000021-0000-0000-0000-000000000012", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 12, "title": "Boxing and Unboxing", "description": "Write a program to demonstrate the concept of boxing and unboxing.", "order_index": 12},
            {"id": "50000021-0000-0000-0000-000000000013", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 13, "title": "Multi-file Program with Scanner", "description": "Create a multi-file program where in one file a string message is taken as input from the user and the function to display the message on the screen is given in another file (make use of Scanner package in this program).", "order_index": 13},
            {"id": "50000021-0000-0000-0000-000000000014", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 14, "title": "Multilevel Package & Fibonacci Reusable Class", "description": "Write a program to create a multilevel package and also creates a reusable class to generate Fibonacci series, where the function to generate Fibonacci series is given in a different file belonging to the same package.", "order_index": 14},
            {"id": "50000021-0000-0000-0000-000000000015", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 15, "title": "Package Protection Levels", "description": "Write a program that creates illustrates different levels of protection in classes/subclasses belonging to same package or different packages", "order_index": 15},
            {"id": "50000021-0000-0000-0000-000000000016", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 16, "title": "DivideByZero Arithmetic Exception", "description": "Write a program – “DivideByZero” that takes two numbers a and b as input, computes a/b, and invokes Arithmetic Exception to generate a message when the denominator is zero.", "order_index": 16},
            {"id": "50000021-0000-0000-0000-000000000017", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 17, "title": "Nested Try Statements", "description": "Write a program to show the use of nested try statements that emphasizes the sequence of checking for catch handler statements.", "order_index": 17},
            {"id": "50000021-0000-0000-0000-000000000018", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 18, "title": "Custom Application Exception", "description": "Write a program to create your own exception types to handle situation specific to your application (Hint: Define a subclass of Exception which itself is a subclass of Throwable).", "order_index": 18},
            {"id": "50000021-0000-0000-0000-000000000019", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 19, "title": "Multiple Thread Priorities", "description": "Write a program to demonstrate priorities among multiple threads.", "order_index": 19},
            {"id": "50000021-0000-0000-0000-000000000020", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 20, "title": "Mouse Handling Events", "description": "Write a program to demonstrate different mouse handling events like mouseClicked(), mouseEntered(), mouseExited(), mousePressed(), mouseReleased() & mouseDragged().", "order_index": 20},
            {"id": "50000021-0000-0000-0000-000000000021", "subject_id": "50000005-0000-0000-0000-000000000005", "exercise_number": 21, "title": "Keyboard Handling Events", "description": "Write a program to demonstrate different keyboard handling events.", "order_index": 21},
        ],
    },
]

SEMESTER_6_SUBJECTS: List[Dict[str, Any]] = [
    {
        "id": "60000001-0000-0000-0000-000000000001",
        "semester_id": SEM_6_ID,
        "name": "Algorithm Design Techniques",
        "code": "Core XIV",
        "subject_type": "theory",
        "order_index": 1,
        "description": "Comprehensive analysis and design of algorithms, complexity bounds, divide-and-conquer, greedy heuristics, dynamic programming, and graph algorithms.",
        "units": [
            {
                "id": "60000011-0000-0000-0000-000000000001",
                "subject_id": "60000001-0000-0000-0000-000000000001",
                "unit_number": 1,
                "title": "Algorithm Specification, Asymptotics & Recurrences",
                "topics": "Algorithm specification, pseudocode, asymptotic analysis, space complexity, time complexity, insertion sort, divide and conquer, recurrence relations, substitution method, recursion tree method and Master method.",
                "order_index": 1,
            },
            {
                "id": "60000011-0000-0000-0000-000000000002",
                "subject_id": "60000001-0000-0000-0000-000000000001",
                "unit_number": 2,
                "title": "Searching, Sorting & Hashing Techniques",
                "topics": "Linear search, binary search, merge sort, quick sort, heap sort, hashing, hash tables, chaining, linear probing, quadratic probing and double hashing.",
                "order_index": 2,
            },
            {
                "id": "60000011-0000-0000-0000-000000000003",
                "subject_id": "60000001-0000-0000-0000-000000000001",
                "unit_number": 3,
                "title": "Greedy Strategies & Dynamic Programming",
                "topics": "Greedy technique, fractional knapsack, job sequencing with deadlines, Huffman codes, dynamic programming, matrix chain multiplication, longest common subsequence and 0/1 knapsack.",
                "order_index": 3,
            },
            {
                "id": "60000011-0000-0000-0000-000000000004",
                "subject_id": "60000001-0000-0000-0000-000000000001",
                "unit_number": 4,
                "title": "Graph Algorithms & Minimum Spanning Trees",
                "topics": "Graph algorithms, topological sorting, minimum spanning trees, Prim's algorithm, Kruskal's algorithm, Bellman-Ford and Dijkstra's algorithm.",
                "order_index": 4,
            },
        ],
        "practicals": [],
    },
    {
        "id": "60000002-0000-0000-0000-000000000002",
        "semester_id": SEM_6_ID,
        "name": "Algorithm Design Lab",
        "code": "BCA 6.2 Lab",
        "subject_type": "practical",
        "order_index": 2,
        "description": "Practical implementation of classical sorting, hashing, greedy choice, dynamic programming, and shortest path graph algorithms.",
        "units": [],
        "practicals": [
            {"id": "60000021-0000-0000-0000-000000000001", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 1, "title": "Insertion Sort", "description": "Write C / C++ Programs to implement Insertion Sort", "order_index": 1},
            {"id": "60000021-0000-0000-0000-000000000002", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 2, "title": "Merge Sort", "description": "Write C / C++ Programs to implement Merge Sort", "order_index": 2},
            {"id": "60000021-0000-0000-0000-000000000003", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 3, "title": "Quick Sort", "description": "Write C / C++ Programs to implement Quick Sort", "order_index": 3},
            {"id": "60000021-0000-0000-0000-000000000004", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 4, "title": "Heap Sort", "description": "Write C / C++ Programs to implement Heap Sort", "order_index": 4},
            {"id": "60000021-0000-0000-0000-000000000005", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 5, "title": "Hashing", "description": "Write C / C++ Programs to implement Hashing", "order_index": 5},
            {"id": "60000021-0000-0000-0000-000000000006", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 6, "title": "Fractional Knapsack", "description": "Write C / C++ Programs to implement Fractional Knapsack", "order_index": 6},
            {"id": "60000021-0000-0000-0000-000000000007", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 7, "title": "Matrix Chain Multiplication", "description": "Write C / C++ Programs to implement Matrix Chain Multiplication", "order_index": 7},
            {"id": "60000021-0000-0000-0000-000000000008", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 8, "title": "Longest Common Subsequence", "description": "Write C / C++ Programs to implement Longest Common Subsequence", "order_index": 8},
            {"id": "60000021-0000-0000-0000-000000000009", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 9, "title": "Huffman Code", "description": "Write C / C++ Programs to implement Huffman Code", "order_index": 9},
            {"id": "60000021-0000-0000-0000-000000000010", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 10, "title": "Prim's Algorithm", "description": "Write C / C++ Programs to implement Prim’s Algorithm", "order_index": 10},
            {"id": "60000021-0000-0000-0000-000000000011", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 11, "title": "Kruskal's Algorithm", "description": "Write C / C++ Programs to implement Krushkal’s Algorithm", "order_index": 11},
            {"id": "60000021-0000-0000-0000-000000000012", "subject_id": "60000002-0000-0000-0000-000000000002", "exercise_number": 12, "title": "Dijkstra's Algorithm", "description": "Write C / C++ Programs to implement Dijkstra’s Algorithm", "order_index": 12},
        ],
    },
    {
        "id": "60000003-0000-0000-0000-000000000003",
        "semester_id": SEM_6_ID,
        "name": "Project Work-I",
        "code": "Core XV",
        "subject_type": "project",
        "order_index": 3,
        "description": "Undergraduate capstone software development project covering full SDLC from problem definition to testing, documentation, and oral defense.",
        "units": [],
        "practicals": [],
        "project_guidelines": {
            "id": "60000031-0000-0000-0000-000000000001",
            "subject_id": "60000003-0000-0000-0000-000000000003",
            "title": "BCA Project Work-I Guidelines & Report Specification",
            "description": "Standard university guidelines for software project documentation, implementation, and evaluation.",
            "report_sections": [
                {"section_number": 1, "title": "Title of the project", "required": True},
                {"section_number": 2, "title": "Declaration", "required": True},
                {"section_number": 3, "title": "Certificate", "required": True},
                {"section_number": 4, "title": "Acknowledgement", "required": True},
                {"section_number": 5, "title": "Abstract", "required": True},
                {"section_number": 6, "title": "Table of Contents", "required": True},
                {"section_number": 7, "title": "Introduction", "required": True},
                {"section_number": 8, "title": "Literature Review", "required": True},
                {"section_number": 9, "title": "Methodology", "required": True},
                {"section_number": 10, "title": "Implementation / Software Development", "required": True},
                {"section_number": 11, "title": "Results", "required": True},
                {"section_number": 12, "title": "Discussion", "required": True},
                {"section_number": 13, "title": "Conclusion", "required": True},
                {"section_number": 14, "title": "References", "required": True},
            ],
            "evaluation_criteria": [
                {"criterion": "Problem formulation and definition", "weight": "20%"},
                {"criterion": "Execution of code and results", "weight": "25%"},
                {"criterion": "Documentation", "weight": "20%"},
                {"criterion": "Clarity in presentation", "weight": "15%"},
                {"criterion": "Viva voce performance", "weight": "20%"},
            ],
        },
    },
]

CANONICAL_SEMESTERS: List[Dict[str, Any]] = [
    {
        "id": SEM_5_ID,
        "name": "Semester V",
        "code": "SEM_5",
        "academic_year": "3rd Year",
        "order_index": 5,
        "description": "BCA Semester V Curriculum comprising Software Engineering, Artificial Intelligence, Data Science, Java, and Java Lab.",
        "subjects": SEMESTER_5_SUBJECTS,
    },
    {
        "id": SEM_6_ID,
        "name": "Semester VI",
        "code": "SEM_6",
        "academic_year": "3rd Year",
        "order_index": 6,
        "description": "BCA Semester VI Curriculum comprising Algorithm Design Techniques, Algorithm Design Lab, and Project Work-I.",
        "subjects": SEMESTER_6_SUBJECTS,
    },
]


def get_canonical_curriculum() -> List[Dict[str, Any]]:
    """Return a deep copy of the canonical BCA Sem V and Sem VI curriculum."""
    import copy
    return copy.deepcopy(CANONICAL_SEMESTERS)


def find_canonical_subject(subject_id: str) -> Optional[Dict[str, Any]]:
    """Lookup a subject by UUID or name across Semester V & VI."""
    for sem in CANONICAL_SEMESTERS:
        for subj in sem["subjects"]:
            if subj["id"] == subject_id or subj["name"].lower() == subject_id.lower():
                import copy
                return copy.deepcopy(subj)
    return None
