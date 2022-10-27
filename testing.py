range = [4, 5, 11, 12, 20, 14, 34, 35, 36, 80, 82, 84, 90, 91]
range = [0]


def compactRange(range):

    # Setup
    range.sort()
    output = ""
    start = range[0]
    last = range[0]

    # Terminator for the end of the range
    range.append(-2) 

    for i in range:

        # If the new number is not adjacent to the old one, we have a completed pair/'island' number
        # And if it is -2, then we hit the end of the list, so add what we have
        if i > last + 1 or i == -2:
            if start == last:
                output = f"{output}, {last}"
            else:
                output = f"{output}, {start}-{last}"
            start = i
            
        last = i

    # Remove the ", " before returning
    return output[2:]



print(compactRange(range))