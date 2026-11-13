"""
SkillSphere Management Command: seed_expanded_assessments
Implements Milestone 3 of the Production Readiness Release:
1. Seeds 5 comprehensive Skill Assessments with 10 high-quality questions each:
   - HTML/CSS (Responsive Design, Flexbox/Grid, Semantics)
   - JavaScript (ES6+, Async/Await, DOM, Closures)
   - C/C++ (Pointers, Memory Management, OOP, Templates)
   - Cloud Fundamentals (AWS/GCP/Azure, IaaS/PaaS, IAM, Storage)
   - Data Science (Pandas, NumPy, EDA, ML Metrics)
2. Expands practical coding exercises across the 6 target courses lacking exercises:
   - Enterprise Java with Spring Boot
   - Flutter & Dart Mobile App Development
   - Modern Web Development with PHP & MySQL
   - C++ OOP & STL
   - Linux System Administration & Bash
   - Computer Networks & Socket Programming
"""

from django.core.management.base import BaseCommand
from django.db import transaction
from assessments.models import SkillAssessment, AssessmentQuestion
from courses.models import Course
from learning.models import Lesson, Exercise


EXPANDED_ASSESSMENTS = [
    {
        'title': 'HTML5 & CSS3 Responsive Engineering Assessment',
        'category': 'HTML_CSS',
        'difficulty': 'Intermediate',
        'time_limit_minutes': 20,
        'questions': [
            {
                'topic': 'Flexbox Layout',
                'text': 'In a flex container with default flex-direction (row), which property aligns flex items along the cross axis (vertical axis)?',
                'a': 'justify-content',
                'b': 'align-items',
                'c': 'flex-basis',
                'd': 'align-content',
                'correct': 'B',
                'explanation': 'justify-content controls alignment along the main axis (horizontal in row mode), while align-items aligns items along the perpendicular cross axis.'
            },
            {
                'topic': 'CSS Grid',
                'text': 'What does `grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));` achieve on a container?',
                'a': 'Creates exactly 4 fixed columns of 250px width.',
                'b': 'Creates an intrinsic responsive grid that wraps columns automatically without needing media queries.',
                'c': 'Forces all columns to span the full viewport width regardless of size.',
                'd': 'Stretches the grid rows to fit vertical height.',
                'correct': 'B',
                'explanation': 'repeat(auto-fit, minmax(250px, 1fr)) dynamically places as many >=250px columns as fit in the container, stretching remaining space evenly across columns.'
            },
            {
                'topic': 'HTML Semantics',
                'text': 'When structuring a blog index page, which HTML5 element is semantically most appropriate for enclosing an individual, self-contained blog post card that could be syndicated?',
                'a': '<section>',
                'b': '<div>',
                'c': '<article>',
                'd': '<aside>',
                'correct': 'C',
                'explanation': '<article> represents a self-contained composition in a document, page, or site, intended to be independently distributable or reusable (e.g. blog post or card).'
            },
            {
                'topic': 'CSS Specificity',
                'text': 'Given the selector `#navbar .nav-item:hover a`, what is its calculated specificity score (IDs, Classes/Attributes/Pseudo-classes, Elements)?',
                'a': '(1, 1, 1)',
                'b': '(1, 2, 1)',
                'c': '(0, 3, 1)',
                'd': '(1, 0, 2)',
                'correct': 'B',
                'explanation': '#navbar is 1 ID; .nav-item and :hover are 2 class/pseudo-class selectors; a is 1 element selector, giving specificity (1, 2, 1).'
            },
            {
                'topic': 'Box Model',
                'text': 'When `box-sizing: border-box` is declared on an element with `width: 300px; padding: 20px; border: 5px solid red;`, what is the rendered total outer width of the element?',
                'a': '350px',
                'b': '300px',
                'c': '250px',
                'd': '325px',
                'correct': 'B',
                'explanation': 'Under border-box, the specified width includes content, padding, and border. Thus the total outer width remains exactly 300px.'
            },
            {
                'topic': 'Responsive Design',
                'text': 'In modern mobile-first responsive web design, which media query strategy is considered standard best practice?',
                'a': 'Using @media (max-width: 768px) to override desktop styling.',
                'b': 'Writing mobile base CSS first and using @media (min-width: ...) to progressively enhance for larger viewports.',
                'c': 'Using JavaScript resize listeners to toggle external stylesheets.',
                'd': 'Hardcoding viewport dimensions in CSS pixel units.',
                'correct': 'B',
                'explanation': 'Mobile-first design defines default styles for small screens without media queries and uses min-width queries to layer desktop features progressively.'
            },
            {
                'topic': 'CSS Variables',
                'text': 'How do you declare a globally scoped CSS custom property named `brand-primary` and access it on a button background?',
                'a': ':root { --brand-primary: #3b82f6; } and background: var(--brand-primary);',
                'b': '$brand-primary: #3b82f6; and background: $brand-primary;',
                'c': 'body { brand-primary: #3b82f6; } and background: get(brand-primary);',
                'd': '@define brand-primary #3b82f6; and background: attr(brand-primary);',
                'correct': 'A',
                'explanation': 'CSS Custom Properties must start with two dashes (--name) and are declared in :root for global cascade. They are retrieved via the var(--name) function.'
            },
            {
                'topic': 'CSS Positioning',
                'text': 'Which CSS positioning value keeps an element in normal document flow until the user scrolls past a defined threshold, after which it behaves like fixed position within its parent?',
                'a': 'position: absolute;',
                'b': 'position: relative;',
                'c': 'position: sticky;',
                'd': 'position: fixed;',
                'correct': 'C',
                'explanation': 'position: sticky behaves like relative until its scroll offset reaches a specified threshold (e.g. top: 0), adhering to the viewport while within its parent bounds.'
            },
            {
                'topic': 'Responsive Images',
                'text': 'Which HTML element or attribute pair allows serving different image files based on device pixel density (DPI) and screen resolution?',
                'a': '<img src="..." alt="..."> only',
                'b': '<img srcset="img-1x.jpg 1x, img-2x.jpg 2x" sizes="...">',
                'c': '<iframe src="...">',
                'd': '<style src="...">',
                'correct': 'B',
                'explanation': 'The srcset attribute on <img> specifies a comma-separated list of image candidates with resolution descriptors (1x, 2x) or width descriptors (w).'
            },
            {
                'topic': 'Performance & Rendering',
                'text': 'Which CSS properties are best suited for performant 60fps animations because they bypass layout recalculation and paint cycles and execute directly on the GPU composite layer?',
                'a': 'top, left, width, height',
                'b': 'margin, padding, border-width',
                'c': 'transform and opacity',
                'd': 'background-color and color',
                'correct': 'C',
                'explanation': 'transform and opacity can be composited entirely on the GPU without triggering browser layout reflow or repaint phases, ensuring smooth 60fps rendering.'
            }
        ]
    },
    {
        'title': 'Modern JavaScript & ES6+ Core Architecture Assessment',
        'category': 'JavaScript',
        'difficulty': 'Intermediate',
        'time_limit_minutes': 25,
        'questions': [
            {
                'topic': 'Event Loop',
                'text': 'What is the exact console output order of: `console.log(1); setTimeout(() => console.log(2), 0); Promise.resolve().then(() => console.log(3)); console.log(4);`?',
                'a': '1, 2, 3, 4',
                'b': '1, 4, 3, 2',
                'c': '1, 4, 2, 3',
                'd': '1, 3, 4, 2',
                'correct': 'B',
                'explanation': 'Synchronous code runs first (1, 4). Microtasks from Promise.then run next (3). Macrotasks from setTimeout execute after all microtasks drain (2).'
            },
            {
                'topic': 'Closures',
                'text': 'What is a closure in JavaScript?',
                'a': 'A function that immediately terminates script execution.',
                'b': 'A function bundled together with references to its surrounding lexical environment (variable scope).',
                'c': 'A built-in method that deep clones JSON objects.',
                'd': 'A private class field prefixed with #.',
                'correct': 'B',
                'explanation': 'A closure is the combination of a function bundled together with references to its surrounding state (the lexical environment), allowing access to outer scope even after the outer function returns.'
            },
            {
                'topic': 'Variable Scoping',
                'text': 'What is the Temporal Dead Zone (TDZ) in ES6 JavaScript?',
                'a': 'The time between when a web page begins downloading and executes DOMContentLoaded.',
                'b': 'The span between entering scope and variable initialization where accessing let or const throws a ReferenceError.',
                'c': 'A setTimeout interval that has exceeded 10 seconds.',
                'd': 'The Garbage Collection pause period during memory deallocation.',
                'correct': 'B',
                'explanation': 'Variables declared with let and const are hoisted to the top of their block, but cannot be accessed until their declaration line is executed. The region before initialization is the TDZ.'
            },
            {
                'topic': 'Asynchronous JS',
                'text': 'What is the main advantage of `Promise.allSettled(promises)` over `Promise.all(promises)`?',
                'a': 'It executes promises sequentially instead of in parallel.',
                'b': 'It never rejects early if one promise fails; it waits for all promises to settle and returns an array of status/value/reason objects.',
                'c': 'It cancels promises that take longer than 1 second.',
                'd': 'It requires no async/await or try/catch blocks.',
                'correct': 'B',
                'explanation': 'Promise.all short-circuits and rejects immediately if any single promise rejects. Promise.allSettled waits for all promises to finish and returns their full outcome array.'
            },
            {
                'topic': 'Prototypes',
                'text': 'In JavaScript prototype inheritance, what does the expression `Object.getPrototypeOf(obj)` return?',
                'a': 'A copy of the object own properties.',
                'b': 'The prototype (internal [[Prototype]]) of the specified object.',
                'c': 'The constructor function string representation.',
                'd': 'A boolean indicating if obj is frozen.',
                'correct': 'B',
                'explanation': 'Object.getPrototypeOf(obj) retrieves the internal [[Prototype]] of obj, which is the object from which obj inherits properties and methods.'
            },
            {
                'topic': 'Arrow Functions',
                'text': 'How do ES6 arrow functions behave differently regarding `this` compared to standard function declarations?',
                'a': 'Arrow functions create a dynamic this bound to the window object.',
                'b': 'Arrow functions do not have their own this; they lexically capture this from the surrounding enclosing scope.',
                'c': 'Arrow functions must be bound explicitly with .bind(this).',
                'd': 'Arrow functions throw a TypeError if this is referenced inside them.',
                'correct': 'B',
                'explanation': 'Arrow functions do not define their own this, arguments, super, or new.target. They inherit this from the surrounding lexical execution context.'
            },
            {
                'topic': 'Object Cloning',
                'text': 'What is the recommended modern native JavaScript standard API for performing deep copies of nested objects with circular reference support?',
                'a': 'JSON.parse(JSON.stringify(obj))',
                'b': 'Object.assign({}, obj)',
                'c': 'structuredClone(obj)',
                'd': '{ ...obj }',
                'correct': 'C',
                'explanation': 'structuredClone() is the native ECMAScript/HTML standard for deep cloning that handles nested objects, arrays, Dates, Maps, Sets, and circular references cleanly.'
            },
            {
                'topic': 'DOM Events',
                'text': 'What is Event Delegation in browser DOM scripting?',
                'a': 'Attaching an event listener to a common ancestor element to leverage event bubbling rather than attaching listeners to each individual child.',
                'b': 'Calling dispatchEvent() on document.body from a Web Worker.',
                'c': 'Delegating rendering logic from CSS to JavaScript canvas.',
                'd': 'Preventing default form submission with event.preventDefault().',
                'correct': 'A',
                'explanation': 'Event delegation takes advantage of event bubbling by putting a single event listener on a parent element to inspect event.target and handle events on children dynamically.'
            },
            {
                'topic': 'Modules',
                'text': 'What is a key difference between ES Modules (ESM) and CommonJS (CJS)?',
                'a': 'ESM is evaluated dynamically at runtime, while CJS is analyzed statically before execution.',
                'b': 'ESM imports (import) are static and evaluated at compile-time/parse-time, enabling tree shaking and dead-code elimination.',
                'c': 'CJS supports browser natively without bundlers; ESM does not.',
                'd': 'ESM requires third-party polyfills in modern Node.js.',
                'correct': 'B',
                'explanation': 'ESM imports are static and declarative, evaluated during module parsing before execution, which allows bundlers to detect unused code and perform tree shaking.'
            },
            {
                'topic': 'Performance Optimization',
                'text': 'When implementing a search auto-complete input that queries an API on keystrokes, which rate-limiting technique delays API invocation until a specified pause after the last keystroke?',
                'a': 'Throttling',
                'b': 'Debouncing',
                'c': 'Memoization',
                'd': 'Virtualization',
                'correct': 'B',
                'explanation': 'Debouncing groups multiple sequential calls into a single execution, resetting its timer with each new invocation until the user stops typing for the specified duration.'
            }
        ]
    },
    {
        'title': 'C & C++ Systems Programming & Memory Mastery Assessment',
        'category': 'CPP',
        'difficulty': 'Intermediate',
        'time_limit_minutes': 25,
        'questions': [
            {
                'topic': 'Pointers & Arrays',
                'text': 'In C and C++, if `int arr[5] = {10, 20, 30, 40, 50}; int *ptr = arr;`, what is the value of `*(ptr + 3)`?',
                'a': '10',
                'b': '30',
                'c': '40',
                'd': '50',
                'correct': 'C',
                'explanation': 'Pointer arithmetic steps by sizeof(int). ptr points to index 0 (10), so *(ptr + 3) accesses arr[3], which is 40.'
            },
            {
                'topic': 'Memory Management',
                'text': 'What is the key difference between `malloc()` and `calloc()` in C standard library?',
                'a': 'malloc() allocates heap memory and zero-initializes all bytes; calloc() leaves memory uninitialized.',
                'b': 'calloc() allocates memory and zero-initializes all bytes, whereas malloc() leaves allocated memory containing arbitrary garbage values.',
                'c': 'calloc() allocates on the stack, while malloc() allocates on the heap.',
                'd': 'malloc() can allocate structs; calloc() cannot.',
                'correct': 'B',
                'explanation': 'calloc(num, size) clears allocated bytes to zero. malloc(size) allocates uninitialized heap memory leaving previous memory contents intact.'
            },
            {
                'topic': 'Smart Pointers',
                'text': 'In modern C++ (C++11 and later), which smart pointer guarantees exclusive, non-copyable ownership of a dynamically allocated heap object?',
                'a': 'std::shared_ptr',
                'b': 'std::weak_ptr',
                'c': 'std::unique_ptr',
                'd': 'std::auto_ptr',
                'correct': 'C',
                'explanation': 'std::unique_ptr enforces strict single ownership of an object through move-only semantics; copy construction and copy assignment are explicitly deleted.'
            },
            {
                'topic': 'Virtual Functions',
                'text': 'Why must a polymorphic base class in C++ declare its destructor as `virtual`?',
                'a': 'To prevent private member variables from being accessed.',
                'b': 'To ensure derived class destructors are called when an object is deleted through a base class pointer, preventing resource leaks.',
                'c': 'To force the compiler to inline the destructor code.',
                'd': 'To permit multiple inheritance of abstract classes.',
                'correct': 'B',
                'explanation': 'Deleting a derived object via a base pointer with a non-virtual destructor results in undefined behavior and skips the derived destructor, leaking derived resources.'
            },
            {
                'topic': 'Memory Safety',
                'text': 'What is a "dangling pointer" in systems programming?',
                'a': 'A pointer initialized to nullptr.',
                'b': 'A pointer that points to a memory location that has already been deallocated or freed.',
                'c': 'A pointer that has circular references in a graph.',
                'd': 'A pointer that points to the beginning of the text segment.',
                'correct': 'B',
                'explanation': 'A dangling pointer occurs when the memory it references is freed or falls out of scope, but the pointer still holds that address. Dereferencing it causes undefined behavior.'
            },
            {
                'topic': 'Move Semantics',
                'text': 'What is the role of `std::move()` in C++11 and newer?',
                'a': 'It physically moves data bytes from RAM to SSD.',
                'b': 'It casts an expression to an rvalue reference (T&&), enabling move constructors and move assignment without deep copying.',
                'c': 'It resets a pointer to null.',
                'd': 'It synchronizes threads across CPU cores.',
                'correct': 'B',
                'explanation': 'std::move is an unconditional cast to an rvalue reference (static_cast<T&&>(val)), signaling to the compiler that the resource may be pilfered rather than copied.'
            },
            {
                'topic': 'Templates',
                'text': 'How do C++ templates achieve type-independent generic programming?',
                'a': 'By converting all types to void* pointers at runtime.',
                'b': 'By generating specialized concrete code for each type instantiation during compilation.',
                'c': 'By interpreting template definitions via an embedded Python VM.',
                'd': 'By boxing primitive types into Object wrappers.',
                'correct': 'B',
                'explanation': 'C++ templates are compile-time constructs. The compiler generates specialized machine code for each unique template argument, avoiding runtime boxing overhead.'
            },
            {
                'topic': 'Const Correctness',
                'text': 'What does `const int * const ptr = &x;` declare?',
                'a': 'A pointer to a constant integer where both the integer value and the pointer address itself are immutable.',
                'b': 'A mutable pointer to a mutable integer.',
                'c': 'A constant pointer to a mutable integer.',
                'd': 'A reference to a static function.',
                'correct': 'A',
                'explanation': 'Reading right to left: ptr is a const pointer (address cannot change) pointing to an int that is const (the referenced integer cannot be modified through this pointer).'
            },
            {
                'topic': 'Rule of Five',
                'text': 'In modern C++, if a class manages a raw resource and defines a custom destructor, which other four special member functions should also be declared or defined?',
                'a': 'main(), init(), cleanup(), and toString()',
                'b': 'Copy constructor, copy assignment operator, move constructor, and move assignment operator.',
                'c': 'operator++, operator--, operator==, and operator!=',
                'd': 'alloc(), dealloc(), lock(), and unlock()',
                'correct': 'B',
                'explanation': 'The Rule of Five dictates that if you need a custom destructor, you almost certainly need to define or explicitly delete copy constructor, copy assignment, move constructor, and move assignment.'
            },
            {
                'topic': 'STL Containers',
                'text': 'What is the algorithmic time complexity of appending an element to the end of a `std::vector` using `push_back()` when reallocation is not triggered?',
                'a': 'O(N)',
                'b': 'O(log N)',
                'c': 'O(1) amortized constant time',
                'd': 'O(N^2)',
                'correct': 'C',
                'explanation': 'std::vector::push_back operates in O(1) amortized time. Even when reallocation occurs, geometric capacity doubling maintains an amortized constant cost per insertion.'
            }
        ]
    },
    {
        'title': 'Cloud Architecture & Infrastructure Fundamentals Assessment',
        'category': 'Cloud_Fundamentals',
        'difficulty': 'Beginner',
        'time_limit_minutes': 20,
        'questions': [
            {
                'topic': 'Cloud Service Models',
                'text': 'Which cloud computing service model provides virtualized computing resources (virtual machines, software-defined networks, and block storage) where the user manages the OS and runtime?',
                'a': 'Software as a Service (SaaS)',
                'b': 'Platform as a Service (PaaS)',
                'c': 'Infrastructure as a Service (IaaS)',
                'd': 'Function as a Service (FaaS)',
                'correct': 'C',
                'explanation': 'IaaS (such as AWS EC2, GCP Compute Engine, Azure VMs) provides raw virtualized hardware, leaving OS patching, runtime installation, and application deployment to the consumer.'
            },
            {
                'topic': 'Shared Responsibility',
                'text': 'Under the Cloud Shared Responsibility Model for IaaS, who is responsible for patching the guest operating system and database software on a virtual machine?',
                'a': 'The Cloud Service Provider (CSP)',
                'b': 'The Customer',
                'c': 'The hardware motherboard manufacturer',
                'd': 'Internet Service Providers (ISPs)',
                'correct': 'B',
                'explanation': 'The CSP is responsible for "Security OF the Cloud" (physical data centers, hypervisors, physical network). The customer is responsible for "Security IN the Cloud" (guest OS, patches, IAM).'
            },
            {
                'topic': 'Storage Systems',
                'text': 'Which cloud storage type is designed for storing massive amounts of unstructured data (such as media files, backups, and static web assets) accessible via HTTP REST APIs with 99.999999999% durability?',
                'a': 'Block Storage (e.g. AWS EBS)',
                'b': 'Object Storage (e.g. AWS S3, Google Cloud Storage)',
                'c': 'Local Ephemeral NVMe Storage',
                'd': 'RAM Disk caches',
                'correct': 'B',
                'explanation': 'Object storage stores data as objects within buckets, accessed over standard HTTPS REST APIs, offering virtually infinite scale and multi-region 11 9s durability.'
            },
            {
                'topic': 'Identity & Access Management',
                'text': 'What is the Principle of Least Privilege in cloud IAM governance?',
                'a': 'Granting full administrative access to all team members during development.',
                'b': 'Granting users and services only the minimum permissions necessary to perform their required tasks.',
                'c': 'Disabling multi-factor authentication (MFA) to minimize login latency.',
                'd': 'Using a single shared root credential for all microservices.',
                'correct': 'B',
                'explanation': 'The Principle of Least Privilege mandates that identities (users, roles, services) be granted only the exact permissions needed to execute their designated duties, mitigating breach blast radius.'
            },
            {
                'topic': 'Networking & VPC',
                'text': 'What is the purpose of a CIDR notation like `10.0.0.0/16` when creating a Virtual Private Cloud (VPC)?',
                'a': 'It sets the maximum bandwidth limit for outgoing internet traffic.',
                'b': 'It defines the IP address range and subnet mask capacity for all resources within the virtual network.',
                'c': 'It encrypts packet payloads using AES-256.',
                'd': 'It designates DNS nameserver routing endpoints.',
                'correct': 'B',
                'explanation': 'Classless Inter-Domain Routing (CIDR) blocks specify the IP prefix and prefix length, establishing the contiguous block of private IP addresses allocated to the VPC (e.g., 65,536 addresses for /16).'
            },
            {
                'topic': 'High Availability',
                'text': 'What distinguishes a Multi-Availability-Zone (Multi-AZ) cloud deployment from a single AZ deployment?',
                'a': 'Multi-AZ distributes workloads across physically isolated data center facilities in the same region with redundant power and fiber, ensuring fault tolerance.',
                'b': 'Multi-AZ is hosted in two different continents.',
                'c': 'Multi-AZ eliminates the need for software database backups.',
                'd': 'Multi-AZ requires manual DNS record updates during failure.',
                'correct': 'A',
                'explanation': 'Availability Zones are distinct, physically separated data centers within a metropolitan geographic region connected by ultra-low-latency fiber. Multi-AZ protects against facility outages.'
            },
            {
                'topic': 'Load Balancing & Scaling',
                'text': 'What is the primary function of an Application Load Balancer (ALB) operating at OSI Layer 7?',
                'a': 'Routing incoming HTTP/HTTPS traffic across backend target instances based on content headers, cookies, and URL path rules.',
                'b': 'Encrypting hard disk partitions at rest.',
                'c': 'Compressing SQL database indexes.',
                'd': 'Transpiling TypeScript to JavaScript.',
                'correct': 'A',
                'explanation': 'Layer 7 load balancers inspect application-level protocol data (HTTP/HTTPS), allowing advanced routing based on request hostnames, paths (/api vs /static), query parameters, and HTTP methods.'
            },
            {
                'topic': 'Serverless Architecture',
                'text': 'What is a "cold start" in serverless functions (e.g. AWS Lambda, Google Cloud Functions)?',
                'a': 'Booting up an on-premise physical rack server after a power cut.',
                'b': 'The latency incurred when the cloud platform initializes a new container instance and runtime environment for an incoming invocation after a period of inactivity.',
                'c': 'Compiling C code with GCC optimization flags disabled.',
                'd': 'A DNS timeout when hitting an expired domain.',
                'correct': 'B',
                'explanation': 'A cold start occurs when a serverless request triggers spin-up of a new isolated container container instance, downloading code and starting the language runtime before handling the request.'
            },
            {
                'topic': 'Infrastructure as Code',
                'text': 'Why is declarative Infrastructure as Code (IaC) using tools like Terraform preferred over manual cloud console clicks?',
                'a': 'It ensures infrastructure is version-controlled, auditable, reproducible, and eliminates human configuration drift.',
                'b': 'It allows servers to run without operating systems.',
                'c': 'It bypasses cloud provider billing engines.',
                'd': 'It automatically translates SQL queries to NoSQL.',
                'correct': 'A',
                'explanation': 'Declarative IaC describes desired end-state configuration in version-controlled files, enabling peer code reviews, automated CI/CD deployments, and reproducible environments without drift.'
            },
            {
                'topic': 'Cost Optimization',
                'text': 'Which EC2 or VM pricing model offers up to 90% cost savings compared to on-demand pricing, in exchange for instances being reclaimable with 2-minute notice when cloud spare capacity is needed?',
                'a': 'Dedicated Hosts',
                'b': 'Reserved Instances',
                'c': 'Spot / Preemptible Instances',
                'd': 'Savings Plans',
                'correct': 'C',
                'explanation': 'Spot (AWS) / Preemptible (GCP) instances leverage unused cloud capacity at steep discounts, making them ideal for fault-tolerant, stateless batch processing and distributed workloads.'
            }
        ]
    },
    {
        'title': 'Data Science, Applied Statistics & Machine Learning Assessment',
        'category': 'Data_Science',
        'difficulty': 'Intermediate',
        'time_limit_minutes': 25,
        'questions': [
            {
                'topic': 'Pandas Indexing',
                'text': 'In a Pandas DataFrame `df`, what is the key difference between `df.loc[]` and `df.iloc[]`?',
                'a': 'loc is label-based indexing; iloc is integer position-based indexing.',
                'b': 'iloc works on columns only; loc works on rows only.',
                'c': 'loc is for numbers; iloc is for strings.',
                'd': 'There is no difference; they are aliases.',
                'correct': 'A',
                'explanation': 'df.loc indexes rows and columns using their index and column labels. df.iloc accesses data strictly by 0-indexed integer position regardless of label names.'
            },
            {
                'topic': 'Data Cleaning',
                'text': 'When dealing with numerical features having missing values (NaNs) in skewed distributions with extreme outliers, which imputation metric is generally preferred over the mean?',
                'a': 'Maximum value',
                'b': 'Median',
                'c': 'Standard Deviation',
                'd': 'Geometric Mean',
                'correct': 'B',
                'explanation': 'The median is robust against extreme outliers and skewness, whereas the arithmetic mean is pulled towards extreme tail values, distorting the central tendency.'
            },
            {
                'topic': 'NumPy Vectorization',
                'text': 'Why is vectorized array computation in NumPy significantly faster than equivalent Python for-loops?',
                'a': 'NumPy operations execute in optimized C/Fortran code over contiguous memory blocks with SIMD hardware instructions, avoiding Python interpreter overhead.',
                'b': 'NumPy converts all data to strings.',
                'c': 'Python loops run inside a web browser sandbox.',
                'd': 'NumPy disables CPU cache checking.',
                'correct': 'A',
                'explanation': 'NumPy arrays store uniform elements in contiguous memory buffers. Operations execute in compiled C routines utilizing CPU SIMD (Single Instruction Multiple Data) vectorization without per-element Python type checking.'
            },
            {
                'topic': 'Model Evaluation',
                'text': 'In high-stakes medical diagnostics where failing to detect a life-threatening disease has catastrophic consequences (false negatives are unacceptable), which classification metric must be prioritized?',
                'a': 'Precision',
                'b': 'Recall (Sensitivity)',
                'c': 'Specificity',
                'd': 'Accuracy',
                'correct': 'B',
                'explanation': 'Recall = TP / (TP + FN). Maximizing recall minimizes False Negatives, ensuring that individuals who actually have the condition are not missed.'
            },
            {
                'topic': 'Bias-Variance Tradeoff',
                'text': 'A deep decision tree that scores 99.8% accuracy on training data but drops to 61.2% accuracy on unseen test data is suffering from what problem?',
                'a': 'High bias (Underfitting)',
                'b': 'High variance (Overfitting)',
                'c': 'Data leakage from test set to train set',
                'd': 'Class imbalance failure',
                'correct': 'B',
                'explanation': 'High variance occurs when a model memorizes the training data noise rather than generalizable underlying patterns, performing exceptionally on train but poorly on test data.'
            },
            {
                'topic': 'Feature Engineering',
                'text': 'What is the purpose of StandardScaler (Z-score normalization) before training distance-based algorithms like KNN, SVM, or PCA?',
                'a': 'To convert categorical variables to one-hot binary columns.',
                'b': 'To rescale features so they have a mean of 0 and standard deviation of 1, preventing high-magnitude features from dominating distance calculations.',
                'c': 'To remove duplicate rows from the dataset.',
                'd': 'To impute missing timestamps.',
                'correct': 'B',
                'explanation': 'Distance metrics (Euclidean, Manhattan) are sensitive to feature scales. Without scaling, a feature measured in tens of thousands will completely dominate a feature measured between 0 and 1.'
            },
            {
                'topic': 'Validation Strategy',
                'text': 'Why is K-Fold Cross Validation superior to a single train-test split for evaluating model performance on modest-sized datasets?',
                'a': 'It ensures every observation is used for both training and validation across K iterations, reducing variance in performance estimates.',
                'b': 'It trains models in zero seconds.',
                'c': 'It eliminates the need for test labels.',
                'd': 'It prevents hyperparameter tuning.',
                'correct': 'A',
                'explanation': 'K-Fold partitions data into K subsets, iteratively training on K-1 folds and validating on the remaining fold. Averaging the K test scores yields a more stable and reliable estimate of generalization.'
            },
            {
                'topic': 'Exploratory Data Analysis',
                'text': 'Which correlation coefficient measures monotonic relationships between variables, including non-linear relationships, based on ranked values?',
                'a': 'Pearson correlation coefficient',
                'b': 'Spearman rank correlation coefficient',
                'c': 'Mean Squared Error',
                'd': 'R-squared goodness of fit',
                'correct': 'B',
                'explanation': 'Spearman rank correlation evaluates how well an arbitrary monotonic function describes the relationship between two variables, using ranks rather than assuming a linear relationship like Pearson.'
            },
            {
                'topic': 'Ensemble Methods',
                'text': 'What is the fundamental difference between Bagging (e.g. Random Forest) and Boosting (e.g. XGBoost, LightGBM)?',
                'a': 'Bagging trains trees sequentially to correct errors; Boosting trains trees in parallel independently.',
                'b': 'Bagging trains trees in parallel on bootstrap samples to reduce variance; Boosting trains trees sequentially where each new model focuses on mistakes of prior models to reduce bias.',
                'c': 'Boosting is only for regression; Bagging is only for classification.',
                'd': 'Bagging uses neural networks; Boosting uses linear models.',
                'correct': 'B',
                'explanation': 'Bagging reduces variance by averaging predictions from multiple independent models trained on bootstrap subsets. Boosting reduces bias by iteratively training weak learners on the residuals of preceding models.'
            },
            {
                'topic': 'Regularization',
                'text': 'How does L1 Regularization (Lasso) differ mathematically and practically from L2 Regularization (Ridge)?',
                'a': 'L1 adds the squared sum of weights and shrinks coefficients evenly; L2 adds absolute weights.',
                'b': 'L1 adds the sum of absolute weight values (L1 norm), driving uninformative feature weights strictly to zero for automated feature selection.',
                'c': 'L1 cannot be used with gradient descent.',
                'd': 'L2 eliminates colinearity by dropping random columns.',
                'correct': 'B',
                'explanation': 'L1 penalty |w| produces diamond-shaped constraint boundaries that intersect axes at zero, setting irrelevant feature coefficients to exactly 0, functioning as automated sparse feature selection.'
            }
        ]
    }
]


EXPANDED_CODING_EXERCISES = [
    {
        'course_slug': 'enterprise-java-spring-boot',
        'lesson_order': 1,
        'title': 'Implement Polymorphic Payment Processing Service in Java',
        'instructions': (
            'Implement an extensible payment processing architecture in Java.\n'
            '1. Define an interface `PaymentGateway` with method `boolean processPayment(double amount)`.\n'
            '2. Implement two classes: `CreditCardGateway` (charges 2% fee) and `CryptoGateway` (charges 0.5% fee).\n'
            '3. In `PaymentService`, inject the gateway and return the total charged formatted to 2 decimals.'
        ),
        'starter_code': (
            'public interface PaymentGateway {\n'
            '    boolean processPayment(double amount);\n'
            '}\n\n'
            '// TODO: Implement CreditCardGateway and CryptoGateway\n'
            'public class PaymentService {\n'
            '    private final PaymentGateway gateway;\n'
            '    public PaymentService(PaymentGateway gateway) {\n'
            '        this.gateway = gateway;\n'
            '    }\n'
            '    public double executeTransaction(double baseAmount) {\n'
            '        // Calculate total with gateway fee and execute\n'
            '        return 0.0;\n'
            '    }\n'
            '}'
        ),
        'expected_output': 'CreditCardGateway processed $102.00 for $100.00 base.',
        'hint': 'Check interface implementation syntax with `implements PaymentGateway`. CreditCard fee is amount * 1.02.',
        'solution': (
            'public class CreditCardGateway implements PaymentGateway {\n'
            '    public boolean processPayment(double amount) { return amount > 0; }\n'
            '}\n'
            '// In PaymentService:\n'
            'public double executeTransaction(double baseAmount) {\n'
            '    double total = baseAmount * 1.02;\n'
            '    gateway.processPayment(total);\n'
            '    return total;\n'
            '}'
        ),
    },
    {
        'course_slug': 'mobile-app-dev-flutter-dart',
        'lesson_order': 1,
        'title': 'Build a Reactive State Container with StreamController in Dart',
        'instructions': (
            'Implement a reactive state manager in Dart using Streams without external packages.\n'
            '1. Create a generic `StateStore<T>` that accepts an initial state.\n'
            '2. Expose a `Stream<T>` stream and a getter `T get state`.\n'
            '3. Provide a `void emit(T newState)` method that updates state and pushes to the stream.\n'
            '4. Provide a `void dispose()` method to close the underlying StreamController.'
        ),
        'starter_code': (
            'import \'dart:async\';\n\n'
            'class StateStore<T> {\n'
            '  // TODO: Add StreamController and state variables\n'
            '  StateStore(T initialState);\n\n'
            '  Stream<T> get stream => throw UnimplementedError();\n'
            '  T get state => throw UnimplementedError();\n\n'
            '  void emit(T newState) {\n'
            '    // TODO: update and broadcast\n'
            '  }\n\n'
            '  void dispose() {\n'
            '    // TODO: close controller\n'
            '  }\n'
            '}'
        ),
        'expected_output': 'StateStore emitted: Counter(count: 1) -> Counter(count: 2)',
        'hint': 'Use `StreamController<T>.broadcast()` so multiple widgets can listen simultaneously.',
        'solution': (
            'class StateStore<T> {\n'
            '  T _state;\n'
            '  final _controller = StreamController<T>.broadcast();\n'
            '  StateStore(this._state);\n'
            '  Stream<T> get stream => _controller.stream;\n'
            '  T get state => _state;\n'
            '  void emit(T newState) {\n'
            '    _state = newState;\n'
            '    _controller.add(newState);\n'
            '  }\n'
            '  void dispose() => _controller.close();\n'
            '}'
        ),
    },
    {
        'course_slug': 'modern-web-development-php-mysql',
        'lesson_order': 1,
        'title': 'Secure SQL Sanitization & PDO Prepared Statements in PHP',
        'instructions': (
            'Write a secure authentication database query function in PHP using PDO.\n'
            '1. Never concatenate user input directly into SQL strings.\n'
            '2. Prepare a statement: `SELECT id, email, password_hash FROM users WHERE email = :email LIMIT 1`.\n'
            '3. Bind `:email` using `PDO::PARAM_STR` and execute.\n'
            '4. Use `password_verify($password, $user[\'password_hash\'])` to validate credentials.'
        ),
        'starter_code': (
            '<?php\n'
            'function authenticateUser(PDO $pdo, string $email, string $password): ?array {\n'
            '    // TODO: Prepare PDO statement with named placeholder :email\n'
            '    // TODO: Execute, fetch associative array, and verify password_verify\n'
            '    return null;\n'
            '}\n'
            '?>'
        ),
        'expected_output': 'User ID 42 authenticated successfully via prepared statement.',
        'hint': 'Use `$stmt = $pdo->prepare(...)` and `$stmt->execute([":email" => $email])`.',
        'solution': (
            '<?php\n'
            'function authenticateUser(PDO $pdo, string $email, string $password): ?array {\n'
            '    $stmt = $pdo->prepare("SELECT id, email, password_hash FROM users WHERE email = :email LIMIT 1");\n'
            '    $stmt->execute([":email" => $email]);\n'
            '    $user = $stmt->fetch(PDO::FETCH_ASSOC);\n'
            '    if ($user && password_verify($password, $user["password_hash"])) {\n'
            '        unset($user["password_hash"]);\n'
            '        return $user;\n'
            '    }\n'
            '    return null;\n'
            '}\n'
            '?>'
        ),
    },
    {
        'course_slug': 'cpp-oop-stl-programming',
        'lesson_order': 1,
        'title': 'Implement Custom RAII Dynamic Buffer with Deep Copy in C++',
        'instructions': (
            'Implement a custom memory-safe dynamic buffer class `DynamicBuffer` in C++ adhering to RAII.\n'
            '1. Allocate raw array `int* data_` on heap of given `size_t capacity_`.\n'
            '2. Implement a destructor `~DynamicBuffer()` that safely deallocates heap memory (`delete[] data_`).\n'
            '3. Implement a deep copy constructor `DynamicBuffer(const DynamicBuffer& other)`.\n'
            '4. Implement a move constructor `DynamicBuffer(DynamicBuffer&& other) noexcept` that pilfers ownership.'
        ),
        'starter_code': (
            '#include <iostream>\n'
            '#include <algorithm>\n\n'
            'class DynamicBuffer {\n'
            'private:\n'
            '    int* data_;\n'
            '    size_t size_;\n'
            'public:\n'
            '    // TODO: Constructor\n'
            '    DynamicBuffer(size_t size);\n'
            '    // TODO: Destructor\n'
            '    ~DynamicBuffer();\n'
            '    // TODO: Copy constructor (deep copy)\n'
            '    DynamicBuffer(const DynamicBuffer& other);\n'
            '    // TODO: Move constructor (pilfer ownership)\n'
            '    DynamicBuffer(DynamicBuffer&& other) noexcept;\n'
            '};'
        ),
        'expected_output': 'DynamicBuffer allocated 1024 ints; deep copy created; source moved cleanly.',
        'hint': 'In move constructor, remember to set `other.data_ = nullptr; other.size_ = 0;` after stealing.',
        'solution': (
            'DynamicBuffer::DynamicBuffer(size_t size) : size_(size), data_(new int[size]()) {}\n'
            'DynamicBuffer::~DynamicBuffer() { delete[] data_; }\n'
            'DynamicBuffer::DynamicBuffer(const DynamicBuffer& other) : size_(other.size_), data_(new int[other.size_]) {\n'
            '    std::copy(other.data_, other.data_ + size_, data_);\n'
            '}\n'
            'DynamicBuffer::DynamicBuffer(DynamicBuffer&& other) noexcept : size_(other.size_), data_(other.data_) {\n'
            '    other.data_ = nullptr;\n'
            '    other.size_ = 0;\n'
            '}'
        ),
    },
    {
        'course_slug': 'linux-system-administration-bash',
        'lesson_order': 1,
        'title': 'Automate High-Frequency Error Log Parser in Bash',
        'instructions': (
            'Write a production-ready Bash script `parse_errors.sh` that analyzes Nginx error logs.\n'
            '1. Accept the log file path as `$1` and exit with code 1 if file is missing.\n'
            '2. Filter lines containing `[error]` or `[crit]` using `grep` or `awk`.\n'
            '3. Extract the offending client IP address and count occurrences.\n'
            '4. Print the top 5 offending IPs sorted in descending order of frequency.'
        ),
        'starter_code': (
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n\n'
            'LOGFILE="${1:-}"\n'
            '# TODO: Validate LOGFILE exists\n'
            '# TODO: Extract errors and output top 5 IP addresses by count\n'
        ),
        'expected_output': 'Top IP offenders:\n  142 192.168.1.105\n   89 10.0.4.22\n   45 172.16.0.8',
        'hint': 'Use `awk \'/\[error\]/ { print $NF }\' "$LOGFILE" | sort | uniq -c | sort -nr | head -n 5`.',
        'solution': (
            '#!/usr/bin/env bash\n'
            'set -euo pipefail\n'
            'LOGFILE="${1:-}"\n'
            'if [[ -z "$LOGFILE" || ! -f "$LOGFILE" ]]; then\n'
            '    echo "Usage: $0 <path-to-nginx-error.log>" >&2\n'
            '    exit 1\n'
            'fi\n'
            'grep -E "\\[(error|crit)\\]" "$LOGFILE" \\\n'
            '    | grep -oE "client: [0-9]+\\.[0-9]+\\.[0-9]+\\.[0-9]+" \\\n'
            '    | awk \'{print $2}\' \\\n'
            '    | sort | uniq -c | sort -nr | head -n 5'
        ),
    },
    {
        'course_slug': 'computer-networks-tcp-ip',
        'lesson_order': 1,
        'title': 'Build a Resilient TCP Echo Socket Client with Reconnection Logic',
        'instructions': (
            'Build a resilient Python socket client using the `socket` module.\n'
            '1. Create a function `send_payload(host, port, message, max_retries=3)`.\n'
            '2. Connect using `socket.AF_INET` and `socket.SOCK_STREAM`.\n'
            '3. Set socket timeout to 5.0 seconds (`sock.settimeout(5.0)`).\n'
            '4. Send encoded bytes and read echo response until complete or connection closes.\n'
            '5. If connection is refused, retry up to `max_retries` with exponential backoff.'
        ),
        'starter_code': (
            'import socket\n'
            'import time\n\n'
            'def send_payload(host: str, port: int, message: str, max_retries: int = 3) -> str:\n'
            '    """Connects to TCP echo server and returns received response."""\n'
            '    # TODO: Implement socket connection, timeouts, and retry logic\n'
            '    return ""\n'
        ),
        'expected_output': 'Echo Response received: "HELLO SPHERE SOCKET" (19 bytes)',
        'hint': 'Wrap `sock.connect((host, port))` in a retry loop catching `(socket.timeout, ConnectionRefusedError)`.',
        'solution': (
            'import socket\n'
            'import time\n\n'
            'def send_payload(host: str, port: int, message: str, max_retries: int = 3) -> str:\n'
            '    for attempt in range(max_retries):\n'
            '        try:\n'
            '            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:\n'
            '                s.settimeout(5.0)\n'
            '                s.connect((host, port))\n'
            '                s.sendall(message.encode("utf-8"))\n'
            '                data = s.recv(4096)\n'
            '                return data.decode("utf-8")\n'
            '        except (socket.timeout, ConnectionRefusedError, OSError) as e:\n'
            '            if attempt == max_retries - 1:\n'
            '                raise\n'
            '            time.sleep(2 ** attempt)\n'
            '    return ""\n'
        ),
    },
]


class Command(BaseCommand):
    help = 'Seeds 5 new Skill Assessments with 10 questions each and adds coding exercises to targeted courses.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE("=== SEEDING EXPANDED SKILL ASSESSMENTS & CODING EXERCISES ==="))

        # Part 1: Seed 5 Skill Assessments
        assessments_created = 0
        questions_created = 0

        with transaction.atomic():
            for item in EXPANDED_ASSESSMENTS:
                assessment, created = SkillAssessment.objects.get_or_create(
                    category=item['category'],
                    defaults={
                        'title': item['title'],
                        'difficulty': item['difficulty'],
                        'time_limit_minutes': item['time_limit_minutes'],
                        'is_active': True,
                    }
                )
                if created:
                    assessments_created += 1
                    self.stdout.write(self.style.SUCCESS(f"+ Created SkillAssessment: {assessment.title} [{assessment.category}]"))
                else:
                    self.stdout.write(f"= Existing SkillAssessment: {assessment.title}")

                for q_idx, q_data in enumerate(item['questions'], start=1):
                    q_obj, q_created = AssessmentQuestion.objects.get_or_create(
                        assessment=assessment,
                        question_text=q_data['text'],
                        defaults={
                            'topic_tag': q_data['topic'],
                            'option_a': q_data['a'],
                            'option_b': q_data['b'],
                            'option_c': q_data['c'],
                            'option_d': q_data['d'],
                            'correct_answer': q_data['correct'],
                            'explanation': q_data['explanation'],
                        }
                    )
                    if q_created:
                        questions_created += 1

        self.stdout.write(self.style.SUCCESS(
            f"Skill Assessments sync complete: {assessments_created} new assessments, {questions_created} new questions created."
        ))

        # Part 2: Seed Coding Exercises in Targeted Courses
        exercises_created = 0

        with transaction.atomic():
            for ex in EXPANDED_CODING_EXERCISES:
                course = Course.objects.filter(slug=ex['course_slug']).first()
                if not course:
                    self.stdout.write(self.style.WARNING(f"Course '{ex['course_slug']}' not found. Skipping exercise."))
                    continue

                lesson = course.lessons.filter(lesson_order=ex['lesson_order']).first()
                if not lesson:
                    lesson = course.lessons.order_by('lesson_order').first()

                if not lesson:
                    self.stdout.write(self.style.WARNING(f"No lessons found in '{course.title}'. Skipping exercise."))
                    continue

                exercise, created = Exercise.objects.get_or_create(
                    lesson=lesson,
                    title=ex['title'],
                    defaults={
                        'instructions': ex['instructions'],
                        'starter_code': ex['starter_code'],
                        'expected_output': ex['expected_output'],
                        'hint': ex['hint'],
                        'solution': ex['solution'],
                        'order': 1,
                    }
                )
                if created:
                    exercises_created += 1
                    self.stdout.write(self.style.SUCCESS(f"+ Added Exercise to '{course.title}': {exercise.title}"))
                else:
                    self.stdout.write(f"= Existing Exercise in '{course.title}': {exercise.title}")

        self.stdout.write(self.style.SUCCESS(
            f"Coding Exercises sync complete: {exercises_created} new exercises created."
        ))
        self.stdout.write(self.style.SUCCESS("=== MILESTONE 3 SEEDING COMPLETED SUCCESSFULLY ==="))
