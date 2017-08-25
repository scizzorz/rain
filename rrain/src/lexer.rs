use std;

#[derive(Debug,Clone,PartialEq)]
pub enum Token {
    Indent,
    Dedent,

    // Literals
    Bool(bool),
    Int(i64),
    Float(f64),
    Str(String),
    Null,

    Keyword(String),
    Identifier(String),

    // Symbols
    Symbol(String),

    // Operators
    Operator(String),

    Newline,
}

use self::Token::*;

const KEYWORDS: [&str ; 14] = [
    "break",
    "catch",
    "continue",
    "else",
    "for",
    "func",
    "if",
    "in",
    "loop",
    "pass",
    "return",
    "save",
    "while",
    "table",
];

fn peek_take_while(it: &mut std::iter::Peekable<std::str::Chars>, f: fn(char) -> bool) -> String {
    use std::fmt::Write;

    let mut res = String::new();
    while let Some(&c) = it.peek() {
        match f(c) {
            true => {
                it.next();
                write!(&mut res, "{}", c).unwrap();
            }
            false => {
                break;
            }
        }
    }
    res
}

fn full_number(digits: &mut String, it: &mut std::iter::Peekable<std::str::Chars>) -> Result<i64, f64> {
    if match it.peek() {
        Some(&c) => {
            match c {
                '0'...'9' | '.' => {
                    it.next();
                    digits.push(c.clone());
                    true
                }
                _ => {
                    false
                }
            }
        }
        _ => {
            false
        }
    } {
        full_number(digits, it)
    } else {
        match digits.contains(".") {
            true => Err(digits.parse::<f64>().unwrap()),
            false => Ok(digits.parse::<i64>().unwrap())
        }
    }
}

pub fn lex(input: &String) -> Result<Vec<Token>, String> {
    let mut result = Vec::new();
    let mut indents: Vec<u32> = vec![0];

    let mut it = input.chars().peekable();
    while let Some(&c) = it.peek() {
        match c {
            '0'...'9' => {
                it.next();
                result.push(match full_number(&mut c.to_string(), &mut it) {
                    Ok(n) => Int(n),
                    Err(n) => Float(n)
                })
            }
            '"' => {
                it.next();
                let string = peek_take_while(&mut it, |c| c != '"');
                it.next();
                result.push(Str(string))
            }
            // :: <= >= > < == != * / + - & | ! $ ~
            // unambiguous operators
            '+' | '*' | '/' | '&' | '|' | '$' | '~' => {
                result.push(Operator(c.to_string()));
                it.next();
            }
            // -> ( ) { } [ ] . , : ; =
            // unambiguous symbols
            '(' | ')' | '{' | '}' | '[' | ']' | '.' | ',' | ';' => {
                result.push(Symbol(c.to_string()));
                it.next();
            }
            ':' => {
                it.next();
                match it.peek() {
                    Some(&':') => {
                        result.push(Operator(String::from("::")));
                        it.next();
                    }
                    _ => {
                        result.push(Symbol(String::from(":")));
                    }
                }
            }
            '=' => {
                it.next();
                match it.peek() {
                    Some(&'=') => {
                        result.push(Operator(String::from("==")));
                        it.next();
                    }
                    _ => {
                        result.push(Symbol(String::from("=")));
                    }
                }
            }
            '-' => {
                it.next();
                match it.peek() {
                    Some(&'>') => {
                        result.push(Symbol(String::from("->")));
                        it.next();
                    }
                    _ => {
                        result.push(Operator(String::from("-")));
                    }
                }
            }
            '!' => {
                it.next();
                match it.peek() {
                    Some(&'=') => {
                        result.push(Operator(String::from("!=")));
                        it.next();
                    }
                    _ => {
                        result.push(Operator(String::from("!")));
                    }
                }
            }
            '<' => {
                it.next();
                match it.peek() {
                    Some(&'=') => {
                        result.push(Operator(String::from("<=")));
                        it.next();
                    }
                    _ => {
                        result.push(Operator(String::from("<")));
                    }
                }
            }
            '>' => {
                it.next();
                match it.peek() {
                    Some(&'=') => {
                        result.push(Operator(String::from(">=")));
                        it.next();
                    }
                    _ => {
                        result.push(Operator(String::from(">")));
                    }
                }
            }
            c if c.is_alphanumeric() => {
                let string: String = peek_take_while(&mut it, |c| c.is_alphanumeric());
                let s = &&string[..];
                result.push(match s {
                    &"true" => { Bool(true) }
                    &"false" => { Bool(false) }
                    &"null" => { Null }
                    _ => {
                        match KEYWORDS.contains(s) {
                            true => { Keyword(string.clone()) }
                            false => { Identifier(string.clone()) }
                        }
                    }
                })
            }
            '\n' => {
                it.next();
                let ws: String = peek_take_while(&mut it, |c| c == ' ');
                let cur_indent = ws.len() as u32;
                match indents.len() {
                    0 => {
                        result.push(Indent);
                        indents.push(cur_indent);
                    }
                    len => {
                        let last_indent = indents[len-1];
                        match cur_indent.partial_cmp(&last_indent) {
                            Some(std::cmp::Ordering::Greater) => {
                                result.push(Indent);
                                indents.push(cur_indent);
                            }
                            Some(std::cmp::Ordering::Less) => {
                                while cur_indent < indents[indents.len()-1] {
                                    result.push(Dedent);
                                    result.push(Newline);
                                    indents.pop();
                                }
                            }
                            _ => {
                                result.push(Newline);
                            }
                        }
                    }
                }
            }
            ' ' => {
                it.next();
            }
            _ => {
                return Err(format!("unexpected char {}", c))
            }
        }
    }
    Ok(result)
}
