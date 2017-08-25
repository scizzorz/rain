//! a parser is a function which takes a token stream and produces a
//! parser result (either an `Ok` ast node or an `Err` string).

//! Parsers are built from smaller parsers.

//! The use of Result allows us to write in a 'and then' kind of style.

//! For example, the grammar `binexpr :: var op var` can be represented in this style as
//! ```
//! fn parse_binexpr(input: &mut TokenStream) -> ParseResult<Binexpr> {
//!     parse_var(input).and_then(|var1| {
//!         parse_op(input).and_then(|op| {
//!             parse_var(input).map(|var2| {
//!                 Binexpr(var1, op, var2)
//!             })
//!         })
//!     })
//! }
//! ```

//! The parsers `parse_var` and `parse_op` are used to build the parser
//! `parse_binexpr`.
//! Each successful parse is passed on to the next part of the parser, creating
//! a pipeline.
//! If a parser fails at any point in the pipeline with an error string,
//! the entire pipeline will stop parsing and fail with the same error string.

//! The function `and_then` is used to continue the parsing with even more
//! (possibly failing) parsers and `map` is used at the end of the pipeline
//! to produce a successful parsing result.

//! To help with the verbosity, the macro `parse_bind!`
//! allow us to simplify this to
//! ```
//! fn parse_binexpr(input: &mut TokenStream) -> ParseResult<Binexpr> {
//!     parse_bind!(
//!     input,
//!     var1 <- parse_var,
//!     op <- parse_op,
//!     var2 <- parse_var,
//!     (Binexpr(var1, op, var2))
//!     )
//! }
//! ```
//! This would translate to the exact same thing as the first, verbose
//! example.

//! There are times when we need to parse many of an item. For these cases
//! we have the function `many` and `many_sep`.
//! `many` turns a parser of an ast node into a parser of a Vec of that ast node.
//! `many_sep` turns a parser of an ast node together with a parser of a separator (e.g., a comma)
//! into a parser of a Vec of that ast node.

// TODO support comments
// TODO support 'ignore indentation' areas

use std;

use lexer::Token;
use lexer::Token::*;

/// A `TokenStream` is an iterator a peekable iterator of tokens
type TokenStream<'a> = std::iter::Peekable<std::slice::Iter<'a, Token>>;
/// A `ParseResult<A>` is either an `Ok(A)` or an `Err(String)`
type ParseResult<A> = Result<A, String>;

#[derive(Debug)]
pub enum AST {
    AStatements(Vec<AStatement>),
}

#[derive(Debug)]
pub enum AStatement {
    ABreak,
    AContinue,
    AFor(AVarPrefix, ABinexpr, ABlock),
    AIf(AIfStmt),
    AElse(AElseStmt),
    AAssign(AAssnPrefix, ACompound),
    AAssignPrefix(AAssnPrefix),
}

#[derive(Debug)]
pub enum AAssnPrefix {
    AAssnPrefixB(ABinexpr),
    AAssnPrefix(Box<AAssnPrefix>, Vec<AAssnPrefix>),
}

#[derive(Debug)]
pub enum ACompound {
    ACompoundF(AFnparams, ACompoundFBody),
    ACompoundC(ABlock),
    ACompoundB(ABinexpr),
}

#[derive(Debug)]
pub enum ACompoundFBody {
    ABinexpr(ABinexpr),
    ABlock(ABlock),
}

#[derive(Debug)]
pub enum AFnparams {
    AFnparams(Vec<Name>),
}


#[derive(Debug)]
pub enum AIfStmt {
    AIfStmt(ABinexpr, ABlock),
}

#[derive(Debug)]
pub enum AElseStmt {
    AElseStmtI(AIfStmt),
    AElseStmtB(ABlock),
}

#[derive(Debug)]
pub enum AVarPrefix {
    AVarPrefixN(Name),
    AVarPrefix(Box<AVarPrefix>, Vec<AVarPrefix>),
}

#[derive(Debug)]
pub enum Op {
    Op(Name)
}

#[derive(Debug)]
pub enum ABinexpr {
    ABinexpr(AUnexpr, Vec<(Op, AUnexpr)>),
}

#[derive(Debug)]
pub enum AUnexpr {
    AUnexpr(Op, Box<AUnexpr>),
    AUnexprS(ASimple),
}

#[derive(Debug)]
pub enum ASimple {
    ASimpleP(APrimary),
}

#[derive(Debug)]
pub enum APrimary {
    APrimary(APrefix, Vec<APrimaryBody>),
}

#[derive(Debug)]
pub enum APrimaryBody {
    AName(Name),
    ANameFnargs(Name, AFnargs),
    AFnargs(AFnargs),
    ABinexpr(ABinexpr),
}

#[derive(Debug)]
pub enum APrefix {
    APrefixNull,
    APrefixB(bool),
    APrefixN(Name),
    APrefixI(i64),
    APrefixF(f64),
    APrefixS(String),
}

#[derive(Debug)]
pub enum AFnargs {
    AFnargs(Vec<ABinexpr>),
}

#[derive(Debug)]
pub enum ABlock {
    ABlock(Vec<AStatement>),
}

type Name = String;

use self::AST::*;
use self::AStatement::*;
use self::ABinexpr::*;
use self::AFnparams::*;
use self::AUnexpr::*;
use self::ASimple::*;
use self::APrimary::*;
use self::AFnargs::*;
use self::APrefix::*;
use self::ABlock::*;
use self::AIfStmt::*;
use self::AElseStmt::*;
use self::AVarPrefix::*;
use self::AAssnPrefix::*;
use self::ACompound::*;
use self::Op::*;

// We get by with only two macros

macro_rules! parse_bind {
    ($input:ident, $var:ident <- $parser:expr, ($next:expr)) => {
        $parser($input).map(|$var| $next)
    };
    ($input:ident, $var:ident <- $parser:expr, $($vars:ident <- $parsers:expr),*, ($next:expr)) => {
        $parser($input)
            .and_then(|$var| parse_bind!($input, $($vars <- $parsers),*, ($next)))
    }
}

macro_rules! mk_parser {
    ($fun:ident, $arg:expr) => {
        |input: &mut TokenStream| $fun(input, $arg)
    };
    ($fun:ident, $arg:expr, $($args:expr),*) => {
        |input: &mut TokenStream| $fun(input, $arg $(, $args),*)
    }
}

/// program :: (stmt NEWLINE)+ EOF
pub fn parse(input: &mut TokenStream) -> ParseResult<AST> {
    parse_bind!(
        input,
        // `many` is not used here because it would silently ignore errors
        // basically, `many` will accept failure and move on, but since
        // this is the top level, we want to expose those errors
        stmts <- parse_statements,
        (AStatements(stmts))
    )
}
fn parse_statements(input: &mut TokenStream) -> ParseResult<Vec<AStatement>> {
    parse_statements_aux(input, Vec::new())
}
fn parse_statements_aux(input: &mut TokenStream, mut acc: Vec<AStatement>) -> ParseResult<Vec<AStatement>> {
    match input.peek() {
        Some(_) => {
            parse_bind!(
                input,
                stmt <- parse_statement,
                _newline <- mk_parser!(parse_token, &Newline),
                rest <- |input| {
                    acc.push(stmt);
                    parse_statements_aux(input, acc)
                },
                (rest)
            )
        }
        // This signifies EOF
        None => {
            Ok(acc)
        }
    }
}

/// Either give an `Ok` token or give an `Err` about reaching end of input
fn peek_next_token<'a>(input: &mut TokenStream<'a>) -> Result<&'a Token, String>{
    match input.peek() {
        Some(&token) => { Ok(token) }
        None => { Err(format!("Unexpected end of input")) }
    }
}

/// Parse many of `f`
fn many<A>(input: &mut TokenStream, f: fn(&mut TokenStream) -> ParseResult<A>) -> ParseResult<Vec<A>> {
    many_aux(input, Vec::new(), f)
}
fn many_aux<A>(input: &mut TokenStream, mut acc: Vec<A>, f: fn(&mut TokenStream) -> ParseResult<A>) -> ParseResult<Vec<A>>{
    match f(input) {
        Ok(res) => {
            acc.push(res);
            many_aux(input, acc, f)
        }
        _ => {
            Ok(acc)
        }
    }
}

/// Parse many of `f` where every pair is separated by `sep`, e.g., the list 1,2,3
fn many_sep<A,B>(input: &mut TokenStream, sep: fn(&mut TokenStream) -> ParseResult<B>, f: fn(&mut TokenStream) -> ParseResult<A>) -> ParseResult<Vec<A>> where A: std::fmt::Debug {
    match f(input) {
        Ok(res) => {
            many_sep_aux(input, vec![res], sep, f)
        }
        _ => {
            Ok(Vec::new())
        }
    }
}
fn many_sep_aux<A,B>(input: &mut TokenStream, mut acc: Vec<A>, sep: fn(&mut TokenStream) -> ParseResult<B>, f: fn(&mut TokenStream) -> ParseResult<A>) -> ParseResult<Vec<A>> where A: std::fmt::Debug {
    match sep(input) {
        Ok(_) => {
            match f(input) {
                Ok(res) => {
                    acc.push(res);
                    many_sep_aux(input, acc, sep, f)
                }
                _ => {
                    Ok(acc)
                }
            }
        }
        Err(_) => {
            Ok(acc)
        }
    }
}

/// Parse the keyword represented by str `kw`
fn parse_keyword(input: &mut TokenStream, kw: &'static str) -> ParseResult<String> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Keyword(ref k) if &k[..] == kw => {
                    input.next();
                    Ok(String::from(kw))
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected {:?}", token, kw))
                }
            }
        })
}

/// Parse any operator and return it's string representation
fn parse_any_operator(input: &mut TokenStream) -> ParseResult<String> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Operator(ref o) => {
                    input.next();
                    Ok(o.clone())
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected operator", token))
                }
            }
        })
}

/// Parse the symbol represented by str `sym`
fn parse_symbol(input: &mut TokenStream, sym: &'static str) -> ParseResult<String> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Symbol(ref s) if &s[..] == sym => {
                    input.next();
                    Ok(String::from(sym))
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected {:?}", token, sym))
                }
            }
        })
}

/// Parse the token `tok`
fn parse_token(input: &mut TokenStream, tok: &'static Token) -> ParseResult<Token> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                t if t == tok => {
                    input.next();
                    Ok(token.clone())
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected {:?}", token, tok))
                }
            }
        })
}

/// stmt :: 'bind' NAME (',' NAME)*
///       | 'break' ('if' binexpr)?
///       | 'continue' ('if' binexpr)?
///       | 'for' var_prefix 'in' binexpr block
///       | if_stmt
///       | else_stmt
///       | 'loop' block
///       | 'pass'
///       | 'return' compound?
///       | 'save' (NAME '=')? compound
///       | 'var' var_prefix ('=' compound)?
///       | 'while' binexpr block
///       | assn_prefix ('=' compound)?
fn parse_statement(input: &mut TokenStream) -> ParseResult<AStatement> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Keyword(ref kw) if &kw[..] == "break" => {
                    input.next();
                    Ok(ABreak)
                },
                &Keyword(ref kw) if &kw[..] == "continue" => {
                    input.next();
                    Ok(AContinue)
                },
                &Keyword(ref kw) if &kw[..] == "for" => {
                    input.next();
                    parse_bind!(input,
                                var_prefix <- parse_var_prefix,
                                _in <- |input| parse_keyword(input, "in"),
                                binexpr <- parse_binexpr,
                                block <- parse_block,
                                (AFor(var_prefix, binexpr, block))
                    )
                },
                &Keyword(ref kw) if &kw[..] == "if" => {
                    input.next();
                    parse_bind!(input,
                                iff <- parse_if,
                                (AIf(iff))
                    )
                },
                &Keyword(ref kw) if &kw[..] == "else" => {
                    input.next();
                    parse_bind!(input,
                                els <- parse_else,
                                (AElse(els))
                    )
                }
                _ => {
                    parse_assn_prefix(input)
                        .and_then(|assn_prefix| {
                            // if we get an '=' then we're parsing an assignment
                            match parse_symbol(input, "=") {
                                Ok(_) => {
                                    parse_compound(input)
                                        .map(|compound| {
                                            AAssign(assn_prefix, compound)
                                        })
                                }
                                _ => {
                                    Ok(AAssignPrefix(assn_prefix))
                                }
                            }
                        })
                }
            }
        })
}

/// assn_prefix :: '[' assn_prefix (',' assn_prefix)* ']'
///              | binexpr
fn parse_assn_prefix(input: &mut TokenStream) -> ParseResult<AAssnPrefix> {
    match parse_symbol(input, "[") {
        Ok(_) => {
            parse_bind!(
                input,
                assn_prefix <- parse_assn_prefix,
                assn_prefixes <- mk_parser!(many, |input| {
                    parse_symbol(input, ",")
                        .and_then(|_| {
                            parse_assn_prefix(input)
                        })
                }),
                _r <- mk_parser!(parse_symbol, "]"),
                (AAssnPrefix(Box::new(assn_prefix), assn_prefixes))
            )
        }
        _ => {
            parse_binexpr(input).map(AAssnPrefixB)
        }
    }
}

/// fnparams :: '(' (NAME (',' NAME)*)? ')'
fn parse_fnparams(input: &mut TokenStream) -> ParseResult<AFnparams> {
    parse_bind!(
        input,
        _l <- mk_parser!(parse_symbol, "("),
        names <- mk_parser!(many_sep, mk_parser!(parse_symbol, ","), parse_name),
        _r <- mk_parser!(parse_symbol, ")"),
        (AFnparams(names))
    )
}

/// compound :: 'func' fnparams ('->' binexpr | block)
///           | 'catch' block
///           | binexpr
fn parse_compound(input: &mut TokenStream) -> ParseResult<ACompound> {
    match parse_keyword(input, "func") {
        Ok(_) => {
            // todo clean this part up a bit
            parse_fnparams(input)
                .and_then(|fnparams| {
                    match parse_symbol(input, "->") {
                        Ok(_) => {
                            parse_binexpr(input)
                                .map(|binexpr| {
                                    ACompoundFBody::ABinexpr(binexpr)
                                })
                        }
                        _ => {
                            parse_block(input)
                                .map(|block| {
                                    ACompoundFBody::ABlock(block)
                                })
                        }
                    }.map(|body| {
                        ACompoundF(fnparams, body)
                    })
                })
        }
        _ => {
            match parse_keyword(input, "catch") {
                Ok(_) => {
                    parse_block(input)
                        .map(ACompoundC)
                }
                _ => {
                    parse_binexpr(input)
                        .map(ACompoundB)
                }
            }
        }
    }
}

/// if :: 'if' binexpr block
fn parse_if(input: &mut TokenStream) -> ParseResult<AIfStmt> {
    parse_bind!(input,
                binexpr <- parse_binexpr,
                block <- parse_block,
                (AIfStmt(binexpr, block))
    )
}

/// else :: 'else' ('if' if_stmt | block)
fn parse_else(input: &mut TokenStream) -> ParseResult<AElseStmt> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Keyword(ref kw) if kw == &String::from("if") => {
                    input.next();
                    parse_if(input).map(AElseStmtI)
                }
                _ => {
                    parse_block(input).map(AElseStmtB)
                }
            }
        })
}

/// var_prefix :: '[' var_prefix (',' var_prefix)* ']'
///             | NAME
fn parse_var_prefix(input: &mut TokenStream) -> ParseResult<AVarPrefix> {
    match parse_symbol(input, "[") {
        Ok(_) => {
            parse_bind!(
                input,
                var_prefix <- parse_var_prefix,
                var_prefixes <- mk_parser!(many, |input| {
                    parse_symbol(input, ",")
                        .and_then(|_| {
                            parse_var_prefix(input)
                        })
                }),
                _r <- mk_parser!(parse_symbol, "]"),
                (AVarPrefix(Box::new(var_prefix), var_prefixes))
            )
        }
        _ => {
            parse_name(input).map(AVarPrefixN)
        }
    }
}

/// binexpr :: unexpr (OPERATOR unexpr)*
fn parse_binexpr(input: &mut TokenStream) -> ParseResult<ABinexpr> {
    parse_bind!(input,
                unexpr <- parse_unexpr,
                tail <- mk_parser!(many, |input| {
                    parse_bind!(
                        input,
                        op <- parse_any_operator,
                        unexpr <- parse_unexpr,
                        ((Op(String::from(op)), unexpr))
                    )
                }),
                (ABinexpr(unexpr, tail))
    )
}

/// unexpr :: ('-' | '!' | '$' | '~') unexpr
///         | simple
fn parse_unexpr(input: &mut TokenStream) -> ParseResult<AUnexpr> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Operator(ref kw) if ["-", "!", "$", "~"].contains(&&kw[..]) => {
                    input.next();
                    parse_unexpr(input)
                        .map(|unexpr| {
                            AUnexpr(Op(kw.clone()), Box::new(unexpr))
                        })
                }
                _ => {
                    parse_simple(input).map(AUnexprS)
                }
            }
        })
}

/// simple :: 'func' fnparams '->' binexpr
///         | array_expr
///         | dict_expr
///         | primary
fn parse_simple(input: &mut TokenStream) -> ParseResult<ASimple> {
    // TODO only support 'primary' here, still lots to do
    parse_primary(input).map(ASimpleP)
}

/// primary :: prefix primary_body*
fn parse_primary(input: &mut TokenStream) -> ParseResult<APrimary> {
    parse_bind!(
        input,
        prefix <- parse_prefix,
        primary_bodies <- mk_parser!(many, parse_primary_body),
        (APrimary(prefix, primary_bodies))
    )
}

/// primary_body :: (fnargs | ':' NAME fnargs | '.' NAME | '[' binexpr ']')*
fn parse_primary_body(input: &mut TokenStream) -> ParseResult<APrimaryBody> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Symbol(ref s) if &s[..] == ":" => {
                    input.next();
                    parse_name(input)
                        .and_then(|name| {
                            parse_fnargs(input)
                                .map(|fnargs| {
                                    APrimaryBody::ANameFnargs(name, fnargs)
                                })
                        })
                }
                &Symbol(ref s) if &s[..] == "." => {
                    input.next();
                    parse_name(input)
                        .map(|name| {
                            APrimaryBody::AName(name)
                        })
                }
                &Symbol(ref s) if &s[..] == "[" => {
                    input.next();
                    parse_binexpr(input)
                        .and_then(|binexpr| {
                            parse_symbol(input, "]")
                                .map(|_| {
                                    APrimaryBody::ABinexpr(binexpr)
                                })
                        })
                }
                &Symbol(ref s) if &s[..] == "(" => {
                    parse_fnargs(input)
                        .map(|fnargs| {
                            APrimaryBody::AFnargs(fnargs)
                        })
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected one of ...", token))
                }

            }
        })
}

/// fnargs :: '(' (binexpr (',' binexpr)*)? ')'
fn parse_fnargs(input: &mut TokenStream) -> ParseResult<AFnargs> {
    parse_bind!(
        input,
        _l <- mk_parser!(parse_symbol, "("),
        binexps <- mk_parser!(many_sep, mk_parser!(parse_symbol, ","), parse_binexpr),
        _r <- mk_parser!(parse_symbol, ")"),
        (AFnargs(binexps))
    )
}

/// prefix :: '(' binexpr ')'
///         | NAME | INT | FLOAT | BOOL | STRING | NULL | (TABLE dict_expr?)
fn parse_prefix(input: &mut TokenStream) -> ParseResult<APrefix> {
    // TODO table not supported yet
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Str(ref s) => {
                    input.next();
                    Ok(APrefixS(s.to_owned()))
                }
                &Int(i) => {
                    input.next();
                    Ok(APrefixI(i))
                }
                &Float(f) => {
                    input.next();
                    Ok(APrefixF(f))
                }
                &Identifier(ref string) => {
                    input.next();
                    Ok(APrefixN(string.clone()))
                }
                &Bool(b) => {
                    input.next();
                    Ok(APrefixB(b))
                }
                &Null => {
                    input.next();
                    Ok(APrefixNull)
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected one of ....", token))
                }
            }
        })
}

/// block :: INDENT (stmt NEWLINE)+ DEDENT
fn parse_block(input: &mut TokenStream) -> ParseResult<ABlock> {
    parse_bind!(
        input,
        _indent <- mk_parser!(parse_token, &Indent),
        stmts <- mk_parser!(many, |input| {
            parse_bind!(
                input,
                stmt <- parse_statement,
                _newline <- mk_parser!(parse_token, &Newline),
                (stmt)
            )
        }),
        _dedent <- mk_parser!(parse_token, &Dedent),
        (ABlock(stmts))
    )
}

/// a name is a string
fn parse_name(input: &mut TokenStream) -> ParseResult<Name> {
    peek_next_token(input)
        .and_then(|token| {
            match token {
                &Identifier(ref string) => {
                    input.next();
                    Ok(string.clone())
                }
                _ => {
                    Err(format!("Unexpected {:?}, expected name", token))
                }
            }
        })
}
