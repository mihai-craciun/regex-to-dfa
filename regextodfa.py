from copy import deepcopy

#Regex validation
def is_valid_regex(regex):
    return valid_brackets(regex) and valid_operations(regex)


def valid_brackets(regex):
    opened_brackets = 0
    for c in regex:
        if c == '(':
            opened_brackets += 1
        if c == ')':
            opened_brackets -= 1
        if opened_brackets < 0:
            print('ERROR missing bracket')
            return False
    if opened_brackets == 0:
        return True
    print('ERROR unclosed brackets')
    return False


def valid_operations(regex):
    for i, c in enumerate(regex):
        if c == '*':
            if i == 0:
                print('ERROR * with no argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR * with no argument at', i)
                return False
        if c == '|':
            if i == 0 or i == len(regex) - 1:
                print('ERROR | with missing argument at', i)
                return False
            if regex[i - 1] in '(|':
                print('ERROR | with missing argument at', i)
                return False
            if regex[i + 1] in ')|':
                print('ERROR | with missing argument at', i)
                return False
    return True

class RegexNode:

    @staticmethod
    def trim_brackets(regex):
        while regex[0] == '(' and regex[-1] == ')' and is_valid_regex(regex[1:-1]):
            regex = regex[1:-1]
        return regex
    
    @staticmethod
    def is_concat(c):
        return c == '(' or RegexNode.is_letter(c)
    
    @staticmethod
    def is_letter(c):
        return c in alphabet

    def __init__(self, regex):
        self.nullable = None
        self.firstpos = []
        self.lastpos = []
        self.item = None
        self.position = None
        self.children = []

        if DEBUG:
            print('Current : '+regex)
        #Check if it is leaf
        if len(regex) == 1 and self.is_letter(regex):
            #Leaf
            self.item = regex
            #Lambda checking
            if use_lambda:
                if self.item == lambda_symbol:
                    self.nullable = True
                else:
                    self.nullable = False
            else:
                self.nullable = False
            return
        
        #It is an internal node
        #Finding the leftmost operators in all three
        kleene = -1
        or_operator = -1
        concatenation = -1
        i = 0

        #Getting the rest of terms    
        while i < len(regex):
            if regex[i] == '(':
                #Composed block
                bracketing_level = 1
                #Skipping the entire term
                i+=1
                while bracketing_level != 0 and i < len(regex):
                    if regex[i] == '(':
                        bracketing_level += 1
                    if regex[i] == ')':
                        bracketing_level -= 1
                    i+=1
            else:
                #Going to the next char
                i+=1
            
            #Found a concatenation in previous iteration
            #And also it was the last element check if breaking
            if i == len(regex):
                break

            #Testing if concatenation
            if self.is_concat(regex[i]):
                if concatenation == -1:
                    concatenation = i
                continue
            #Testing for kleene
            if regex[i] == '*':
                if kleene == -1:
                    kleene = i
                continue
            #Testing for or operator
            if regex[i] == '|':
                if or_operator == -1:
                    or_operator = i
        
        #Setting the current operation by priority
        if or_operator != -1:
            #Found an or operation
            self.item = '|'
            self.children.append(RegexNode(self.trim_brackets(regex[:or_operator])))
            self.children.append(RegexNode(self.trim_brackets(regex[(or_operator+1):])))
        elif concatenation != -1:
            #Found a concatenation
            self.item = '.'
            self.children.append(RegexNode(self.trim_brackets(regex[:concatenation])))
            self.children.append(RegexNode(self.trim_brackets(regex[concatenation:])))
        elif kleene != -1:
            #Found a kleene
            self.item = '*'
            self.children.append(RegexNode(self.trim_brackets(regex[:kleene])))

    def calc_functions(self, pos, followpos):
        if self.is_letter(self.item):
            #Is a leaf
            self.firstpos = [pos]
            self.lastpos = [pos]
            self.position = pos
            #Add the position in the followpos list
            followpos.append([self.item,[]])
            return pos+1
        #Is an internal node
        for child in self.children:
            pos = child.calc_functions(pos, followpos)
        #Calculate current functions

        if self.item == '.':
            #Is concatenation
            #Firstpos
            if self.children[0].nullable:
                self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            else:
                self.firstpos = deepcopy(self.children[0].firstpos)
            #Lastpos
            if self.children[1].nullable:
                self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            else:
                self.lastpos = deepcopy(self.children[1].lastpos)
            #Nullable
            self.nullable = self.children[0].nullable and self.children[1].nullable
            #Followpos
            for i in self.children[0].lastpos:
                for j in self.children[1].firstpos:
                    if j not in followpos[i][1]:
                        followpos[i][1] = sorted(followpos[i][1] + [j])

        elif self.item == '|':
            #Is or operator
            #Firstpos
            self.firstpos = sorted(list(set(self.children[0].firstpos + self.children[1].firstpos)))
            #Lastpos
            self.lastpos = sorted(list(set(self.children[0].lastpos + self.children[1].lastpos)))
            #Nullable
            self.nullable = self.children[0].nullable or self.children[1].nullable

        elif self.item == '*':
            #Is kleene
            #Firstpos
            self.firstpos = deepcopy(self.children[0].firstpos)
            #Lastpos
            self.lastpos = deepcopy(self.children[0].lastpos)
            #Nullable
            self.nullable = True
            #Followpos
            for i in self.children[0].lastpos:
                for j in self.children[0].firstpos:
                    if j not in followpos[i][1]:
                        followpos[i][1] = sorted(followpos[i][1] + [j])

        return pos

    def write_level(self, level):
        print(str(level) + ' ' + self.item, self.firstpos, self.lastpos, self.nullable, '' if self.position == None else self.position)
        for child in self.children:
            child.write_level(level+1)

class RegexTree:

    def __init__(self, regex):
        self.root = RegexNode(regex)
        self.followpos = []
        self.functions()
    
    def write(self):
        self.root.write_level(0)

    def functions(self):
        positions = self.root.calc_functions(0, self.followpos)   
        if DEBUG == True:
            print(self.followpos)
    
    def toDfa(self):

        def contains_hashtag(q):
            for i in q:
                if self.followpos[i][0] == '#':
                    return True
            return False

        M = [] #Marked states
        Q = [] 
        V = alphabet - {'#'}
        d = []
        F = []
        q0 = self.root.firstpos

        Q.append(q0)
        if contains_hashtag(q0):
            F.append(Q.index(q0))
        
        while len(Q) - len(M) > 0:
            #There exists one unmarked
            q = [i for i in Q if i not in M][0]
            M.append(q)
            for a in V:
                U = []
                #Compute U
                #foreach i in state
                for i in q:
                    #if i has label a
                    if self.followpos[i][0] == a:
                        U = U + self.followpos[i][1]
                U = sorted(list(set(U)))
                if U not in Q:
                    Q.append(U)
                    if contains_hashtag(U):
                        F.append(Q.index(U))
                if not Q.index(U) in d:
                    d.append({})
                d[Q.index(q)][a] = Q.index(U)
        
        return Dfa(len(Q),V,d,Q.index(q0),F)

        
class Dfa:

    def __init__(self,Q,V,d,q0,F):
        self.Q = Q
        self.V = V
        self.d = d
        self.q0 = q0
        self.F = F

    def run(self, text):
        #Checking if the input is in the current alphabet
        if len(set(text) - self.V) != 0:
            #Not all the characters are in the language
            print('ERROR characters',(set(text)-self.V),'are not in the automata\'s alphabet')
            exit(0)
        
        #Running the automata
        q = self.q0
        for i in text:
            #Execute transition
            q = self.d[q][i]
        
        if q in self.F:
            print('Message accepted!')
        else:
            print('Message NOT accepted')

#Preprocessing Functions
def preprocess(regex):
    regex = clean_kleene(regex)
    regex = regex.replace(' ','')
    regex = '(' + regex + ')' + '#'
    while '()' in regex:
        regex = regex.replace('()','')
    return regex

def clean_kleene(regex):
    for i in range(0, len(regex) - 1):
        while i < len(regex) - 1 and regex[i + 1] == regex[i] and regex[i] == '*':
            regex = regex[:i] + regex[i + 1:]
    return regex

def gen_alphabet(regex):
    return set(regex) - set('()|*')

#Settings
DEBUG = False
use_lambda = False
lambda_symbol = '_'
alphabet = None

#Main
regex = '(aa|b)*ab(bb|a)*'
regex = preprocess(regex)
alphabet = gen_alphabet(regex)

#Check
if not is_valid_regex(regex):
    exit(0)

#Construct
tree = RegexTree(regex)
# tree.write()
dfa = tree.toDfa()

#Test
message = 'baaab'
dfa.run(message)
