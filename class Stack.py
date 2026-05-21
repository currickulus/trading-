class Stack:
   
    def __init__(self):
        
        self.items = []

    def is_empty(self):
       
        return len(self.items) == 0

    def push(self, item):
       
        self.items.append(item)

    def pop(self):
        
        if self.is_empty():
            raise IndexError("pop from empty stack")
        return self.items.pop()

def print_stack(stack, label):
   
    print(f"\n{label}:")
    if stack.is_empty():
        print("  [Empty]")
        return
    print("  <-- Top")
    for item in reversed(stack.items):  # Print from top to bottom
        print(f"  [{item}]")
    print("  <-- Bottom")

def main():
    
    # Create the original stack and push 1, 2, 3
    original_stack = Stack()
    original_stack.push(1)  # Bottom
    original_stack.push(2)
    original_stack.push(3)  # Top
    
    # Print the original stack
    print_stack(original_stack, "Original Stack")
    
    # Create a new stack and reverse the elements
    reversed_stack = Stack()
    # First, collect elements in a list by popping (top to bottom: 3, 2, 1)
    temp_list = []
    while not original_stack.is_empty():
        temp_list.append(original_stack.pop())
    # Push elements back to original_stack to restore it
    for item in reversed(temp_list):
        original_stack.push(item)
    # Push elements to reversed_stack in order (3, 2, 1) so 1 is at the top
    for item in temp_list:
        reversed_stack.push(item)
    
    # Print the reversed stack
    print_stack(reversed_stack, "Reversed Stack")

if __name__ == "__main__":
    main()