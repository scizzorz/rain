keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
name 'print'
symbol '('
string 'LHS < RHS'
symbol ')'
newline
keyword 'let'
symbol '['
name 'a'
symbol ']'
symbol '='
symbol '['
int 1
symbol ','
int 2
symbol ','
int 3
symbol ']'
newline
name 'print'
symbol '('
name 'a'
symbol ')'
newline
name 'print'
symbol '('
string 'LHS == RHS'
symbol ')'
newline
keyword 'let'
symbol '['
name 'b'
symbol ','
name 'c'
symbol ']'
symbol '='
symbol '['
int 1
symbol ','
int 2
symbol ']'
newline
name 'print'
symbol '('
name 'b'
symbol ')'
newline
name 'print'
symbol '('
name 'c'
symbol ')'
newline
name 'print'
symbol '('
string 'LHS > RHS'
symbol ')'
newline
keyword 'let'
symbol '['
name 'd'
symbol ','
name 'e'
symbol ','
name 'f'
symbol ']'
symbol '='
symbol '['
int 1
symbol ']'
newline
name 'print'
symbol '('
name 'd'
symbol ')'
newline
name 'print'
symbol '('
name 'e'
symbol ')'
newline
name 'print'
symbol '('
name 'f'
symbol ')'
newline
name 'print'
symbol '('
string 'Nested LHS == Nested RHS'
symbol ')'
newline
keyword 'let'
symbol '['
name 'g'
symbol ','
symbol '['
name 'h'
symbol ','
name 'i'
symbol ']'
symbol ','
name 'j'
symbol ']'
symbol '='
symbol '['
int 1
symbol ','
symbol '['
int 2
symbol ','
int 3
symbol ']'
symbol ','
int 4
symbol ']'
newline
name 'print'
symbol '('
name 'g'
symbol ')'
newline
name 'print'
symbol '('
name 'h'
symbol ')'
newline
name 'print'
symbol '('
name 'i'
symbol ')'
newline
name 'print'
symbol '('
name 'j'
symbol ')'
newline
name 'print'
symbol '('
string 'Nested LHS != Nested RHS'
symbol ')'
newline
keyword 'let'
symbol '['
symbol '['
name 'k'
symbol ','
name 'l'
symbol ']'
symbol ','
name 'm'
symbol ','
name 'n'
symbol ']'
symbol '='
symbol '['
int 1
symbol ','
symbol '['
int 2
symbol ','
int 3
symbol ']'
symbol ','
int 4
symbol ']'
newline
name 'print'
symbol '('
name 'k'
symbol ')'
newline
name 'print'
symbol '('
name 'l'
symbol ')'
newline
name 'print'
symbol '('
name 'm'
symbol '['
int 0
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'm'
symbol '['
int 1
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'n'
symbol ')'
newline
name 'print'
symbol '('
string 'LHS == Nested RHS'
symbol ')'
newline
keyword 'let'
symbol '['
name 'o'
symbol ','
name 'p'
symbol ','
name 'q'
symbol ']'
symbol '='
symbol '['
int 1
symbol ','
symbol '['
int 2
symbol ','
int 3
symbol ']'
symbol ','
symbol '['
int 4
symbol ','
symbol '['
int 5
symbol ']'
symbol ']'
symbol ']'
newline
name 'print'
symbol '('
name 'o'
symbol ')'
newline
name 'print'
symbol '('
name 'p'
symbol '['
int 0
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'p'
symbol '['
int 1
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'q'
symbol '['
int 0
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'q'
symbol '['
int 1
symbol ']'
symbol '['
int 0
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
string 'Swap 1'
symbol ')'
newline
symbol '['
name 'b'
symbol ','
name 'c'
symbol ']'
symbol '='
symbol '['
name 'c'
symbol ','
name 'b'
symbol ']'
newline
name 'print'
symbol '('
name 'b'
symbol ')'
newline
name 'print'
symbol '('
name 'c'
symbol ')'
newline
name 'print'
symbol '('
string 'Swap 2'
symbol ')'
newline
keyword 'let'
name 'x'
symbol '='
symbol '['
int 1
symbol ','
int 2
symbol ']'
newline
symbol '['
name 'x'
symbol '['
int 1
symbol ']'
symbol ','
name 'x'
symbol '['
int 0
symbol ']'
symbol ']'
symbol '='
name 'x'
newline
name 'print'
symbol '('
name 'x'
symbol '['
int 0
symbol ']'
symbol ')'
newline
name 'print'
symbol '('
name 'x'
symbol '['
int 1
symbol ']'
symbol ')'
newline
dedent
newline
EOF
