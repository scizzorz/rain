keyword 'import'
name 'macros'
newline
keyword 'let'
name 'fudge'
symbol '='
symbol '['
string 'one'
symbol ','
string 'two'
symbol ','
string 'three'
symbol ']'
newline
keyword 'let'
name 'node'
symbol '='
symbol '{'
name 'tag'
symbol '='
string 'node'
symbol ','
name 'body'
symbol '='
string 'body'
symbol ','
symbol '}'
newline
keyword 'let'
name 'person'
symbol '='
symbol '{'
name 'name'
symbol '='
string 'Phil'
symbol ','
name 'age'
symbol '='
int 47
symbol ','
name 'kids'
symbol '='
int 4
symbol ','
name 'married'
symbol '='
bool True
symbol ','
symbol '}'
newline
keyword 'let'
name 'square'
symbol '='
keyword 'func'
symbol '('
name 'n'
symbol ')'
indent
keyword 'let'
name 'ret'
symbol '='
symbol '@'
name 'macros'
symbol '.'
name 'case'
name 'n'
indent
int 1
symbol '='
int 1
newline
int 2
symbol '='
int 4
newline
int 3
symbol '='
int 9
newline
int 4
symbol '='
int 16
newline
name ''
symbol '='
int 0
newline
int 5
symbol '='
int 25
newline
dedent
newline
keyword 'return'
name 'ret'
newline
dedent
newline
keyword 'let'
name 'main'
symbol '='
keyword 'func'
symbol '('
symbol ')'
indent
symbol '@'
name 'macros'
symbol '.'
name 'printall'
symbol '('
name 'fudge'
symbol '['
int 0
symbol ']'
symbol ','
name 'fudge'
symbol '['
int 1
symbol ']'
symbol ','
name 'fudge'
symbol '['
int 2
symbol ']'
symbol ')'
newline
symbol '@'
name 'macros'
symbol '.'
name 'printall'
symbol '('
string '----'
symbol ','
name 'node'
symbol '.'
name 'tag'
symbol ','
name 'node'
symbol '.'
name 'body'
symbol ')'
newline
symbol '@'
name 'macros'
symbol '.'
name 'call'
name 'print'
indent
string 'Hello!'
newline
dedent
newline
symbol '@'
name 'macros'
symbol '.'
name 'match'
symbol '{'
name 'string'
symbol '='
name 'name'
symbol ','
name 'number'
symbol '='
name 'age'
symbol '}'
name 'person'
newline
name 'print'
symbol '('
name 'string'
symbol ')'
newline
name 'print'
symbol '('
name 'number'
symbol ')'
newline
name 'print'
symbol '('
name 'square'
symbol '('
int 3
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'square'
symbol '('
int 4
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'square'
symbol '('
int 5
symbol ')'
symbol ')'
newline
name 'print'
symbol '('
name 'square'
symbol '('
int 6
symbol ')'
symbol ')'
newline
dedent
newline
EOF
