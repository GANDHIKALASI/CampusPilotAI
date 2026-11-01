-- =============================================================================
-- CAMPUSPILOT AI — MIGRATION 006: ACADEMIC CURRICULUM STRUCTURE (SEM V & VI)
-- Implements complete BCA Semester V and Semester VI academic hierarchy:
-- Semesters -> Subjects -> Units / Practicals / Project Guidelines
-- Links documents and document chunks to academic subjects and units.
-- =============================================================================

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- -----------------------------------------------------------------------------
-- 1. SEMESTERS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.semesters (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    code TEXT UNIQUE NOT NULL,
    title TEXT NOT NULL,
    semester_number INTEGER NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

-- -----------------------------------------------------------------------------
-- 2. SUBJECTS TABLE
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.subjects (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    semester_id UUID NOT NULL REFERENCES public.semesters(id) ON DELETE CASCADE,
    code TEXT,
    name TEXT NOT NULL,
    subject_type TEXT NOT NULL DEFAULT 'theory' CHECK (subject_type IN ('theory', 'practical', 'project')),
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_subjects_semester_id ON public.subjects(semester_id);

-- -----------------------------------------------------------------------------
-- 3. UNITS TABLE (Theory Subjects)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.units (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    unit_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    topics TEXT NOT NULL,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_units_subject_id ON public.units(subject_id);

-- -----------------------------------------------------------------------------
-- 4. PRACTICALS TABLE (Lab Exercises)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.practicals (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    exercise_number INTEGER NOT NULL,
    title TEXT NOT NULL,
    description TEXT,
    display_order INTEGER NOT NULL DEFAULT 0,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_practicals_subject_id ON public.practicals(subject_id);

-- -----------------------------------------------------------------------------
-- 5. PROJECT GUIDELINES TABLE (Project Work)
-- -----------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS public.project_guidelines (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    subject_id UUID NOT NULL REFERENCES public.subjects(id) ON DELETE CASCADE,
    report_sections JSONB NOT NULL DEFAULT '[]'::jsonb,
    evaluation_criteria JSONB NOT NULL DEFAULT '[]'::jsonb,
    created_at TIMESTAMPTZ NOT NULL DEFAULT timezone('utc', now())
);

CREATE INDEX IF NOT EXISTS idx_project_guidelines_subject_id ON public.project_guidelines(subject_id);

-- -----------------------------------------------------------------------------
-- 6. LINK DOCUMENTS & DOCUMENT_CHUNKS TO ACADEMIC STRUCTURE
-- -----------------------------------------------------------------------------
DO $$
BEGIN
    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'semester_id'
    ) THEN
        ALTER TABLE public.documents ADD COLUMN semester_id UUID REFERENCES public.semesters(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'subject_id'
    ) THEN
        ALTER TABLE public.documents ADD COLUMN subject_id UUID REFERENCES public.subjects(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'documents' AND column_name = 'unit_id'
    ) THEN
        ALTER TABLE public.documents ADD COLUMN unit_id UUID REFERENCES public.units(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'semester_id'
    ) THEN
        ALTER TABLE public.document_chunks ADD COLUMN semester_id UUID REFERENCES public.semesters(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'subject_id'
    ) THEN
        ALTER TABLE public.document_chunks ADD COLUMN subject_id UUID REFERENCES public.subjects(id) ON DELETE SET NULL;
    END IF;

    IF NOT EXISTS (
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = 'public' AND table_name = 'document_chunks' AND column_name = 'unit_id'
    ) THEN
        ALTER TABLE public.document_chunks ADD COLUMN unit_id UUID REFERENCES public.units(id) ON DELETE SET NULL;
    END IF;
END $$;

CREATE INDEX IF NOT EXISTS idx_documents_subject_id ON public.documents(subject_id);
CREATE INDEX IF NOT EXISTS idx_documents_semester_id ON public.documents(semester_id);
CREATE INDEX IF NOT EXISTS idx_document_chunks_subject_id ON public.document_chunks(subject_id);

-- -----------------------------------------------------------------------------
-- 7. ROW LEVEL SECURITY (RLS) POLICIES
-- Academic curriculum data is public/read-only for all students
-- -----------------------------------------------------------------------------
ALTER TABLE public.semesters ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.subjects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.units ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.practicals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.project_guidelines ENABLE ROW LEVEL SECURITY;

DROP POLICY IF EXISTS "Allow read access to semesters" ON public.semesters;
CREATE POLICY "Allow read access to semesters" ON public.semesters FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read access to subjects" ON public.subjects;
CREATE POLICY "Allow read access to subjects" ON public.subjects FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read access to units" ON public.units;
CREATE POLICY "Allow read access to units" ON public.units FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read access to practicals" ON public.practicals;
CREATE POLICY "Allow read access to practicals" ON public.practicals FOR SELECT USING (true);

DROP POLICY IF EXISTS "Allow read access to project guidelines" ON public.project_guidelines;
CREATE POLICY "Allow read access to project guidelines" ON public.project_guidelines FOR SELECT USING (true);

-- -----------------------------------------------------------------------------
-- 8. SEED DATA: SEMESTER V & SEMESTER VI (EXACT SYLLABUS FIDELITY)
-- -----------------------------------------------------------------------------
DO $$
DECLARE
    v_sem5_id UUID;
    v_sem6_id UUID;
    v_se_id UUID;
    v_ai_id UUID;
    v_ds_id UUID;
    v_java_id UUID;
    v_java_lab_id UUID;
    v_algo_id UUID;
    v_algo_lab_id UUID;
    v_proj_id UUID;
BEGIN
    -- 1. Semesters
    INSERT INTO public.semesters (id, code, title, semester_number)
    VALUES ('55555555-5555-5555-5555-555555555555', 'SEM_5', 'Semester V', 5)
    ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title;

    INSERT INTO public.semesters (id, code, title, semester_number)
    VALUES ('66666666-6666-6666-6666-666666666666', 'SEM_6', 'Semester VI', 6)
    ON CONFLICT (code) DO UPDATE SET title = EXCLUDED.title;

    SELECT id INTO v_sem5_id FROM public.semesters WHERE code = 'SEM_5';
    SELECT id INTO v_sem6_id FROM public.semesters WHERE code = 'SEM_6';

    -- 2. Semester V Subjects
    -- Subject 1: Software Engineering (Core XI)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '50000001-0000-0000-0000-000000000001',
        v_sem5_id,
        'Core XI',
        'Software Engineering',
        'theory',
        'Principles of software engineering, development life cycle models, project management, requirement specification, design, coding, testing and maintenance.',
        1
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_se_id;

    -- Subject 2: Introduction to Artificial Intelligence (Core XII (A))
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '50000002-0000-0000-0000-000000000002',
        v_sem5_id,
        'Core XII (A)',
        'Introduction to Artificial Intelligence',
        'theory',
        'Core AI principles, state-space search, informed/heuristic search, knowledge representation, reasoning under uncertainty, NLP and expert systems. Note: In the official university syllabus, AI is elective option (A) under Core XII alongside Data Science (B); CampusPilot provides both as distinct full subjects.',
        2
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_ai_id;

    -- Subject 3: Introduction to Data Science (Core XII (B))
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '50000003-0000-0000-0000-000000000003',
        v_sem5_id,
        'Core XII (B)',
        'Introduction to Data Science',
        'theory',
        'Data scientist tool box, R programming, data acquisition, cleaning, tidy data, and exploratory data analysis with multivariate visualization. Note: In the official university syllabus, Data Science is elective option (B) under Core XII alongside AI (A); CampusPilot provides both as distinct full subjects.',
        3
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_ds_id;

    -- Subject 4: Programming in Java (Major XIII)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '50000004-0000-0000-0000-000000000004',
        v_sem5_id,
        'Major XIII',
        'Programming in Java',
        'theory',
        'Object-oriented programming in Java, class hierarchies, interfaces, collections, streams, multithreading, networking, and JDBC.',
        4
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_java_id;

    -- Subject 5: Java Programming Lab (BCA 6.1 Lab)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '50000005-0000-0000-0000-000000000005',
        v_sem5_id,
        'BCA 6.1 Lab',
        'Java Programming Lab',
        'practical',
        'Laboratory exercises covering core Java programming, OOP, strings, constructors, packages, exceptions, threads, events, and I/O.',
        5
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_java_lab_id;

    -- 3. Semester VI Subjects
    -- Subject 1: Algorithm Design Techniques (Core XIV)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '60000001-0000-0000-0000-000000000001',
        v_sem6_id,
        'Core XIV',
        'Algorithm Design Techniques',
        'theory',
        'Asymptotic analysis, divide-and-conquer, searching, sorting, hashing, greedy algorithms, dynamic programming, and graph algorithms.',
        1
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_algo_id;

    -- Subject 2: Algorithm Design Lab (BCA 6.2 Lab)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '60000002-0000-0000-0000-000000000002',
        v_sem6_id,
        'BCA 6.2 Lab',
        'Algorithm Design Lab',
        'practical',
        'Hands-on implementation of sorting, hashing, greedy strategies, dynamic programming, and graph algorithms in C / C++.',
        2
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_algo_lab_id;

    -- Subject 3: Project Work-I (Core XV / BCA 6.3)
    INSERT INTO public.subjects (id, semester_id, code, name, subject_type, description, display_order)
    VALUES (
        '60000003-0000-0000-0000-000000000003',
        v_sem6_id,
        'Core XV',
        'Project Work-I',
        'project',
        'Independent academic project under faculty guidance with report submission, code execution, viva voce, and external evaluation.',
        3
    ) ON CONFLICT (id) DO UPDATE SET name = EXCLUDED.name, description = EXCLUDED.description
    RETURNING id INTO v_proj_id;

    -- -------------------------------------------------------------------------
    -- 4. Units for Theory Subjects
    -- -------------------------------------------------------------------------

    -- Software Engineering Units
    DELETE FROM public.units WHERE subject_id = '50000001-0000-0000-0000-000000000001';
    INSERT INTO public.units (subject_id, unit_number, title, topics, display_order) VALUES
    ('50000001-0000-0000-0000-000000000001', 1, 'Unit I: Introduction and Software Lifecycle Models', 'Evolution of Software to an Engineering Discipline, Software Development Projects, Exploratory Style of Software Development, Emergence of Software Engineering, Changes in Software Development Practices, Computer Systems Engineering. Software Lifecycle Models: Waterfall Model and its Extensions, Rapid Application Development (RAD), Agile Development Models, Spiral Model.', 1),
    ('50000001-0000-0000-0000-000000000001', 2, 'Unit II: Software Project Management', 'Software Project Management Complexities, Responsibilities of a Software Project Manager, Project Planning, Metrics for Project Size Estimation, Project Estimation Techniques, Empirical Estimation Techniques, COCOMO, Halstead''s Software Science, Staffing Level Estimation, Scheduling, Organization and Team Structures, Staffing, Risk Management, Software Configuration Management.', 2),
    ('50000001-0000-0000-0000-000000000001', 3, 'Unit III: Requirement Analysis, Specification and Software Design', 'Requirements Gathering and Analysis, Software Requirement Specifications (SRS), Formal System Specification Axiomatic Specification, Algebraic Specification, Executable Specification and 4GL. Software Design: Design Process, Characterize a Good Software Design, Cohesion and Coupling, Layered Arrangements of Modules, Approaches to Software Design (Function Oriented & Object-Oriented).', 3),
    ('50000001-0000-0000-0000-000000000001', 4, 'Unit IV: Coding, Testing and Maintenance', 'Coding: Code Review, Software Documentation, Testing, Unit Testing, Black Box and White Box Testing, Debugging, Program Analysis Tools, Integration Testing, System Testing, Software Maintenance.', 4);

    -- Introduction to Artificial Intelligence Units
    DELETE FROM public.units WHERE subject_id = '50000002-0000-0000-0000-000000000002';
    INSERT INTO public.units (subject_id, unit_number, title, topics, display_order) VALUES
    ('50000002-0000-0000-0000-000000000002', 1, 'Unit I: Introduction to AI and Uninformed Search', 'Introduction to AI, Scope of AI, Characteristics of AI problems, Turing test, Concept of Intelligent agents, Approaches to AI problem-solving, State space search, production system, Uninformed search: Breadth-First Search (BFS), Depth-First Search (DFS), Iterative deepening, bidirectional and beam search.', 1),
    ('50000002-0000-0000-0000-000000000002', 2, 'Unit II: Informed and Heuristic Search', 'Informed/Heuristic search: Generate-and-Test, Hill climbing, Best-first search, A* algorithm, Problem reduction, AO*, Constraint satisfaction, Solution of CSP using search, Means-End analysis.', 2),
    ('50000002-0000-0000-0000-000000000002', 3, 'Unit III: Knowledge Representation and Reasoning Under Uncertainty', 'Knowledge Representation: Propositional logic and Predicate logic along with their resolution principles, Unification algorithm, forward and backward chaining and conflict resolution, Semantic nets, Frames, Conceptual dependencies, Scripts. Reasoning under uncertainty: Bayesian Belief networks, Dempster Shafer theory.', 3),
    ('50000002-0000-0000-0000-000000000002', 4, 'Unit IV: Natural Language Processing and Expert Systems', 'Natural language processing: Introduction, Levels of knowledge in language understanding, Phases of Natural language understanding, top-down and bottom-up parsing, transition networks. Expert Systems: Introduction, Architecture, Expert system development cycle, Examples of ES: Mycin and Dendral.', 4);

    -- Introduction to Data Science Units
    DELETE FROM public.units WHERE subject_id = '50000003-0000-0000-0000-000000000003';
    INSERT INTO public.units (subject_id, unit_number, title, topics, display_order) VALUES
    ('50000003-0000-0000-0000-000000000003', 1, 'Unit I: Data Scientist''s Tool Box', 'Turning data into actionable knowledge, introduction to the tools that are used in building data analysis software: version control, markdown, git, GitHub, R, and RStudio.', 1),
    ('50000003-0000-0000-0000-000000000003', 2, 'Unit II: R Programming Basics', 'Overview of R, R data types and objects, reading and writing data, Control structures, functions, scope rules, dates and times, Loop functions, debugging tools, Simulation, code profiling.', 2),
    ('50000003-0000-0000-0000-000000000003', 3, 'Unit III: Getting and Cleaning Data', 'Obtaining data from the web, from APIs, from databases and other sources in various formats, basics of data cleaning and making data "tidy".', 3),
    ('50000003-0000-0000-0000-000000000003', 4, 'Unit IV: Exploratory Data Analysis', 'Essential exploratory techniques for summarizing data, applied before formal modeling commences, eliminating or sharpening potential hypotheses about the world that can be addressed by the data, common multivariate statistical techniques used to visualize high-dimensional data.', 4);

    -- Programming in Java Units
    DELETE FROM public.units WHERE subject_id = '50000004-0000-0000-0000-000000000004';
    INSERT INTO public.units (subject_id, unit_number, title, topics, display_order) VALUES
    ('50000004-0000-0000-0000-000000000004', 1, 'Unit I: Introduction to Java', 'Java History, Architecture and Features, Understanding the semantic and syntax differences between C++ and Java, Compiling and Executing a Java Program, Variables, Constants, Keywords (super, this, final, abstract, static, extends, implements, interface), Data Types, Wrapper class, Operators (Arithmetic, Logical and Bitwise) and Expressions, Comments, Doing Basic Program Output, Decision Making Constructs (conditional statements and loops) and Nesting, Java Methods (Defining, Scope, Passing and Returning Arguments, Type Conversion and Type Checking, Built-in Java Class Methods). Input through keyboard using Command line Argument, the Scanner class, BufferedReader class.', 1),
    ('50000004-0000-0000-0000-000000000004', 2, 'Unit II: Object-Oriented Programming Overview', 'Principles of Object-Oriented Programming, Defining & Using Classes, Class Variables & Methods, Objects, Object reference, Objects as parameters, final classes, Garbage Collection. Constructor- types of constructors, this keyword, super keyword. Method overloading and Constructor overloading. Aggregation vs Inheritance, Inheritance: extends vs implements, types of Inheritance, Interface, Up-Casting, Down-Casting, Auto-Boxing, Enumerations, Polymorphism, Method Overriding and restrictions. Package: Pre-defined packages and Custom packages.', 2),
    ('50000004-0000-0000-0000-000000000004', 3, 'Unit III: Arrays, Strings, and Java I/O', 'Arrays: Creating & Using Arrays (1D, 2D, 3D and Jagged Array), Array of Object, Referencing Arrays Dynamically. Strings and I/O: Java Strings: The Java String class, Creating & Using String Objects, Manipulating Strings, String Immutability & Equality, Passing Strings To & From Methods, StringBuffer Classes and StringBuilder Classes. IO package: Understanding Streams, File class and its methods, Creating, Reading, Writing using classes: Byte and Character streams, FileOutputStream, FileInputStream, FileWriter, FileReader, InputStreamReader, PrintStream, PrintWriter. Compressing and Uncompressing File.', 3),
    ('50000004-0000-0000-0000-000000000004', 4, 'Unit IV: Exception Handling, Multithreading, Networking and JDBC', 'Exception Handling, Threading, Networking and Database Connectivity: Exception types, uncaught exceptions, throw, built-in exceptions, Creating your own exceptions; Multithreading: The Thread class and Runnable interface, creating single and multiple threads, Thread prioritization, synchronization and communication, suspending/resuming threads. Using java.net package, Overview of TCP/IP and Datagram programming. Accessing and manipulating databases using JDBC.', 4);

    -- Algorithm Design Techniques Units
    DELETE FROM public.units WHERE subject_id = '60000001-0000-0000-0000-000000000001';
    INSERT INTO public.units (subject_id, unit_number, title, topics, display_order) VALUES
    ('60000001-0000-0000-0000-000000000001', 1, 'Unit I: Algorithm Specification and Analysis Framework', 'Algorithm specification, Pseudocode, Space complexity, Time Complexity, Asymptotic Notation (O, Omega, Theta), Divide and Conquer: General method, Applications: Insertion Sort, Recurrence relations: substitution method, recursion-tree method, Master method.', 1),
    ('60000001-0000-0000-0000-000000000001', 2, 'Unit II: Searching, Sorting and Hashing', 'Searching and Sorting: Linear search, Binary search, Merge Sort, Quick Sort, Heap Sort. Hashing: Hash tables, Hash functions, Collision Resolution: Separate Chaining, Open Addressing (Linear probing, Quadratic probing, Double hashing).', 2),
    ('60000001-0000-0000-0000-000000000001', 3, 'Unit III: Greedy Technique and Dynamic Programming', 'Greedy Technique: General Method, Applications: Fractional Knapsack Problem, Job Sequencing with Deadlines, Huffman Codes. Dynamic Programming: General Method, Applications: Matrix Chain Multiplication, longest common subsequence, 0/1 Knapsack.', 3),
    ('60000001-0000-0000-0000-000000000001', 4, 'Unit IV: Graph Algorithms', 'Graph Algorithms, Topological sort, Minimum Spanning Trees: Prim''s and Kruskal''s algorithm, Single-source shortest paths: Bellman-Ford algorithm, Dijkstra''s algorithm.', 4);

    -- -------------------------------------------------------------------------
    -- 5. Practicals for Java Programming Lab (All 21 Exercises)
    -- -------------------------------------------------------------------------
    DELETE FROM public.practicals WHERE subject_id = '50000005-0000-0000-0000-000000000005';
    INSERT INTO public.practicals (subject_id, exercise_number, title, description, display_order) VALUES
    ('50000005-0000-0000-0000-000000000005', 1, 'Command Line Arguments Sum', 'To find the sum of any number of integers entered as command line arguments.', 1),
    ('50000005-0000-0000-0000-000000000005', 2, 'Factorial of a Number', 'To find the factorial of a given number.', 2),
    ('50000005-0000-0000-0000-000000000005', 3, 'Decimal to Binary Conversion', 'To convert a decimal to binary number.', 3),
    ('50000005-0000-0000-0000-000000000005', 4, 'Prime Number Check', 'To check if a number is prime or not, by taking the number as input from the keyboard.', 4),
    ('50000005-0000-0000-0000-000000000005', 5, 'Interactive Integer Summation', 'To find the sum of any number of integers interactively, i.e., entering every number from the keyboard, whereas the total number of integers is given as a command line argument.', 5),
    ('50000005-0000-0000-0000-000000000005', 6, 'String and StringBuffer Operations', 'Write a program that show working of different functions of String and StringBuffer class like setCharAt(), setLength(), append(), insert(), concat() and equals().', 6),
    ('50000005-0000-0000-0000-000000000005', 7, 'Distance Class & Object Instantiation', 'Write a program to create a "distance" class with methods where distance is computed in terms of feet and inches, how to create objects of a class and to see the use of this pointer.', 7),
    ('50000005-0000-0000-0000-000000000005', 8, 'Distance Class Constructor & Cloning', 'Modify the "distance" class by creating constructor for assigning values (feet and inches) to the distance object. Create another object and assign second object as reference variable to another object reference variable. Further create a third object which is a clone of the first object.', 8),
    ('50000005-0000-0000-0000-000000000005', 9, 'Function Overloading & Type Conversion', 'Write a program to show that during function overloading, if no matching argument is found, then Java will apply automatic type conversions (from lower to higher data type).', 9),
    ('50000005-0000-0000-0000-000000000005', 10, 'Access Specifiers & Pass-by-Value/Reference', 'Write a program to show the difference between public and private access specifiers. The program should also show that primitive data types are passed by value and objects are passed by reference and to learn use of final keyword.', 10),
    ('50000005-0000-0000-0000-000000000005', 11, 'Static Functions & Varargs', 'Write a program to show the use of static functions and to pass variable length arguments in a function.', 11),
    ('50000005-0000-0000-0000-000000000005', 12, 'Autoboxing and Unboxing', 'Write a program to demonstrate the concept of boxing and unboxing.', 12),
    ('50000005-0000-0000-0000-000000000005', 13, 'Multi-File Program & Scanner', 'Create a multi-file program where in one file a string message is taken as input from the user and the function to display the message on the screen is given in another file (make use of Scanner package in this program).', 13),
    ('50000005-0000-0000-0000-000000000005', 14, 'Multilevel Package & Fibonacci Series', 'Write a program to create a multilevel package and also creates a reusable class to generate Fibonacci series, where the function to generate Fibonacci series is given in a different file belonging to the same package.', 14),
    ('50000005-0000-0000-0000-000000000005', 15, 'Package Protection Levels', 'Write a program that illustrates different levels of protection in classes/subclasses belonging to same package or different packages.', 15),
    ('50000005-0000-0000-0000-000000000005', 16, 'DivideByZero ArithmeticException', 'Write a program "DivideByZero" that takes two numbers a and b as input, computes a/b, and invokes Arithmetic Exception to generate a message when the denominator is zero.', 16),
    ('50000005-0000-0000-0000-000000000005', 17, 'Nested Try Statements', 'Write a program to show the use of nested try statements that emphasizes the sequence of checking for catch handler statements.', 17),
    ('50000005-0000-0000-0000-000000000005', 18, 'Custom Exception Types', 'Write a program to create your own exception types to handle situation specific to your application (Hint: Define a subclass of Exception which itself is a subclass of Throwable).', 18),
    ('50000005-0000-0000-0000-000000000005', 19, 'Multithreading Priorities', 'Write a program to demonstrate priorities among multiple threads.', 19),
    ('50000005-0000-0000-0000-000000000005', 20, 'Mouse Handling Events', 'Write a program to demonstrate different mouse handling events like mouseClicked(), mouseEntered(), mouseExited(), mousePressed(), mouseReleased() & mouseDragged().', 20),
    ('50000005-0000-0000-0000-000000000005', 21, 'Keyboard Handling Events', 'Write a program to demonstrate different keyboard handling events.', 21);

    -- -------------------------------------------------------------------------
    -- 6. Practicals for Algorithm Design Lab (All 12 Exercises)
    -- -------------------------------------------------------------------------
    DELETE FROM public.practicals WHERE subject_id = '60000002-0000-0000-0000-000000000002';
    INSERT INTO public.practicals (subject_id, exercise_number, title, description, display_order) VALUES
    ('60000002-0000-0000-0000-000000000002', 1, 'Insertion Sort', 'Write C / C++ Programs to implement Insertion Sort', 1),
    ('60000002-0000-0000-0000-000000000002', 2, 'Merge Sort', 'Write C / C++ Programs to implement Merge Sort', 2),
    ('60000002-0000-0000-0000-000000000002', 3, 'Quick Sort', 'Write C / C++ Programs to implement Quick Sort', 3),
    ('60000002-0000-0000-0000-000000000002', 4, 'Heap Sort', 'Write C / C++ Programs to implement Heap Sort', 4),
    ('60000002-0000-0000-0000-000000000002', 5, 'Hashing', 'Write C / C++ Programs to implement Hashing', 5),
    ('60000002-0000-0000-0000-000000000002', 6, 'Fractional Knapsack', 'Write C / C++ Programs to implement Fractional Knapsack', 6),
    ('60000002-0000-0000-0000-000000000002', 7, 'Matrix Chain Multiplication', 'Write C / C++ Programs to implement Matrix Chain Multiplication', 7),
    ('60000002-0000-0000-0000-000000000002', 8, 'Longest Common Subsequence', 'Write C / C++ Programs to implement Longest Common Subsequence', 8),
    ('60000002-0000-0000-0000-000000000002', 9, 'Huffman Code', 'Write C / C++ Programs to implement Huffman Code', 9),
    ('60000002-0000-0000-0000-000000000002', 10, 'Prim''s Algorithm', 'Write C / C++ Programs to implement Prim''s Algorithm', 10),
    ('60000002-0000-0000-0000-000000000002', 11, 'Kruskal''s Algorithm', 'Write C / C++ Programs to implement Kruskal''s Algorithm', 11),
    ('60000002-0000-0000-0000-000000000002', 12, 'Dijkstra''s Algorithm', 'Write C / C++ Programs to implement Dijkstra''s Algorithm', 12);

    -- -------------------------------------------------------------------------
    -- 7. Project Work-I Guidelines & Evaluation Criteria
    -- -------------------------------------------------------------------------
    DELETE FROM public.project_guidelines WHERE subject_id = '60000003-0000-0000-0000-000000000003';
    INSERT INTO public.project_guidelines (subject_id, report_sections, evaluation_criteria) VALUES
    (
        '60000003-0000-0000-0000-000000000003',
        '[
            {"section_number": 1, "title": "Title of the project", "description": "Official title reflecting project scope and problem domain."},
            {"section_number": 2, "title": "Declaration", "description": "Formal student declaration of original work under faculty supervision."},
            {"section_number": 3, "title": "Certificate", "description": "Faculty project guide certificate approving the completed report."},
            {"section_number": 4, "title": "Acknowledgement", "description": "Acknowledgment of guidance, institution, and resource support."},
            {"section_number": 5, "title": "Abstract", "description": "Brief summary of project objectives, methods, architecture, and key findings."},
            {"section_number": 6, "title": "Table of Contents", "description": "Organized list of chapters, sections, sub-sections, and page references."},
            {"section_number": 7, "title": "Introduction", "description": "Background context, domain motivation, problem statement, and primary objectives."},
            {"section_number": 8, "title": "Literature Review", "description": "Survey of existing research, relevant systems, baseline theories, and comparative analysis."},
            {"section_number": 9, "title": "Methodology", "description": "System architecture, design patterns, data flow, algorithms, and development tools/stack."},
            {"section_number": 10, "title": "Implementation / Software Development", "description": "Core software modules, database schema, algorithm implementation, and interface workflows."},
            {"section_number": 11, "title": "Results", "description": "Demonstration of operational system, experimental benchmarks, tables, and output figures."},
            {"section_number": 12, "title": "Discussion", "description": "Interpretation of results, system constraints, trade-offs, and alignment with initial goals."},
            {"section_number": 13, "title": "Conclusion", "description": "Summary of achievements, impact, limitations, and roadmap for future enhancement."},
            {"section_number": 14, "title": "References", "description": "Scholarly and technical citations adhering to standard formats (IEEE, APA, MLA)."}
        ]'::jsonb,
        '[
            {"criteria_number": 1, "title": "Problem Formulation and Definition", "weight": "20%", "description": "Clarity of problem statement, academic relevance, and scope boundary definition."},
            {"criteria_number": 2, "title": "Execution of Code & Results", "weight": "30%", "description": "Working software implementation, code quality, test cases, and functional correctness."},
            {"criteria_number": 3, "title": "Documentation", "weight": "20%", "description": "Thoroughness, formatting standard, diagrams, and completeness of the written report."},
            {"criteria_number": 4, "title": "Clarity in Presentation", "weight": "15%", "description": "Effectiveness in explaining architecture, design choices, and demonstrating system features."},
            {"criteria_number": 5, "title": "Performance in the Viva Voce", "weight": "15%", "description": "Technical mastery, ability to defend design decisions, and answers to examiner inquiries."}
        ]'::jsonb
    );

END $$;
