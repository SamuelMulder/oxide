"""
Copyright (c) 2014 Sandia Corporation. 
Under the terms of Contract DE-AC04-94AL85000 with Sandia Corporation, 
the U.S. Government retains certain rights in this software.

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.
"""

######### FUNCTIONS THAT RETURN THE VALUE OF A SINGLE BIT  ###############################
def bit_4(byts):  
    """ Given at least a 1 byte value return the value of extracted bit 4
    """
    return ( ord(byts[0]) & 0b10000 ) >> 4

def bit_5(byts):  
    """ Given at least a 1 byte value return the value of extracted bit 5
    """
    return ( ord(byts[0]) & 0b100000 ) >> 5
    
def bit_6(byts):  
    """ Given at least a 1 byte value return the value of extracted bit 6
    """
    return ( ord(byts[0]) & 0b100000 ) >> 6

def bit_7(byts):  
    """ Given at least a 1 byte value return the value of extracted bit 7
    """
    return ( ord(byts[0]) & 0b10000000 ) >> 7

def bit_8(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 8
    """
    return ord(byts[1]) & 0b1

def bit_9(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 9
    """
    return ( ord(byts[1]) & 0b10 ) >> 1
    
def bit_10(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 10
    """
    return ( ord(byts[1]) & 0b100 ) >> 2
    
def bit_11(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 11
    """
    return ( ord(byts[1]) & 0b1000 ) >> 3
    
def bit_12(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 12
    """
    return ( ord(byts[1]) & 0b10000 ) >> 4

def bit_13(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 13
    """
    return ( ord(byts[1]) & 0b100000 ) >> 5
    
def bit_14(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 14
    """
    return ( ord(byts[1]) & 0b1000000 ) >> 6
        
def bit_15(byts):  
    """ Given at least a 2 byte value return the value of extracted bit 15
    """
    return ( ord(byts[1]) & 0b10000000 ) >> 7
    
def bit_20(byts):  
    """ Given at least a 3 byte value return the value of extracted bit 20
    """
    return ( ord(byts[2]) & 0b10000 ) >> 4

def bit_21(byts):  
    """ Given at least a 3 byte value return the value of extracted bit 21
    """
    return ( ord(byts[2]) & 0b100000 ) >> 5

def bit_22(byts):  
    """ Given at least a 3 byte value return the value of extracted bit 22
    """
    return ( ord(byts[2]) & 0b1000000 ) >> 6

def bit_23(byts):  
    """ Given at least a 3 byte value return the value of extracted bit 23
    """
    return ( ord(byts[2]) & 0b10000000 ) >> 7
    
def bit_24(byts):  
    """ Given at least a 4 byte value return the value of extracted bit 24
    """
    return ord(byts[3]) & 0b1 

def bit_25(byts):  
    """ Given at least a 4 byte value return the value of extracted bit 25
    """
    return ( ord(byts[3]) & 0b10 ) >> 1

def bit_26(byts):  
    """ Given at least a 4 byte value return the value of extracted bit 26
    """
    return ( ord(byts[3]) & 0b100 ) >> 2

def bit_27(byts):  
    """ Given at least a 4 byte value return the value of extracted bit 27
    """
    return ( ord(byts[3]) & 0b1000 ) >> 3

######### FUNCTIONS THAT RETURN THE VALUE OF A BIT RANGE #################################
def bits_0_3(byts):
    """ Given at least a 1 byte return the value of extracted bits 0 to 3
    """
    return ord(byts[0]) & 0b1111 
    
def bits_0_7(byts):
    """ Given at least a 1 byte return the value of extracted bits 0 to 7
    """
    return ord(byts[0]) 

def bits_0_10(byts):
    """ Given at least a 2 byte value return the value of extracted bits 0 to 11
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[1]) & 0b111) << 8 ) + ord(byts[0])
    
def bits_0_11(byts):
    """ Given at least a 2 byte value return the value of extracted bits 0 to 11
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[1]) & 0b1111) << 8 ) + ord(byts[0])
        
def bits_0_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 0 to 15
        In this case the extracted bits crosses a byte boundaries
    """
    return (ord(byts[1]) << 8 ) + ord(byts[0])

def bits_0_23(byts):
    """ Given at least a 3 byte value return the value of extracted bits 0 to 15
        In this case the extracted bits crosses two byte boundaries
    """
    return (ord(byts[2]) << 16 ) + (ord(byts[1]) << 8 ) + ord(byts[0])

def bits_3_6(byts):
    """ Given at least a 1 byte value return the value of extracted bits 3 to 6
    """
    return ( ord(byts[0]) & 0b111000) >> 3

def bits_4_6(byts):
    """ Given at least a 1 byte value return the value of extracted bits 4 to 6
    """
    return ( ord(byts[0]) & 0b1110000) >> 4
    
def bits_4_7(byts):
    """ Given at least a 1 byte value return the value of extracted bits 4 to 7
    """
    return ( ord(byts[0]) & 0b11110000) >> 4

def bits_5_6(byts):
    """ Given at least a 1 byte value return the value of extracted bits 5 to 6
    """
    return (ord(byts[0]) & 0b1100000) >> 5

def bits_6_7(byts):
    """ Given at least a 1 byte value return the value of extracted bits 6 to 7
    """
    return (ord(byts[0]) & 0b11000000) >> 6

def bits_6_9(byts):
    """ Given at least a 2 byte value return the value of extracted bits 6 to 9
        In this case the extracted bits crosses a byte boundaries
    """
    return ((ord(byts[1]) & 0b11) << 2) + ((ord(byts[0]) & 0b11000000) >> 6)

def bits_7_11(byts):
    """ Given at least a 2 byte value return the value of extracted bits 7 to 11
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[1]) & 0b1111) << 1 ) + ( (ord(byts[0]) & 0b10000000) >> 7 )

def bits_8_11(byts):
    """ Given at least a 2 byte value return the value of extracted bits 8 to 11
    """
    return ord(byts[1]) & 0b1111 

def bits_10_11(byts):
    """ Given at least a 2 byte value return the value of extracted bits 10 to 11
    """
    return (ord(byts[1]) & 0b1100 ) >> 2 

def bits_10_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 10 to 15
    """
    return (ord(byts[1]) & 0b11111100 ) >> 2 
    
def bits_11_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 11 to 15
    """
    return (ord(byts[1]) & 0b11111000 ) >> 3 

def bits_12_14(byts):
    """ Given at least a 2 byte value return the value of extracted bits 12 to 14
    """
    return (ord(byts[1]) & 0b1110000 ) >> 4 
    
def bits_12_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 12 to 15
    """
    return (ord(byts[1]) & 0b11110000 ) >> 4 
    
def bits_13_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 13 to 15
    """
    return (ord(byts[1]) & 0b11100000 ) >> 5 
    
def bits_14_15(byts):
    """ Given at least a 2 byte value return the value of extracted bits 14 to 15
    """
    return (ord(byts[1]) & 0b11000000 ) >> 6 
    
def bits_16_17(byts):
    """ Given at least a 3 byte value return the value of extracted bits 16 to 17
    """
    return ord(byts[2]) & 0b11 

def bits_16_19(byts):
    """ Given at least a 3 byte value return the value of extracted bits 16 to 19
    """
    return ord(byts[2]) & 0b1111 
    
def bits_16_25(byts):
    """ Given at least a 4 byte value return the value of extracted bits 16 to 25
    """
    return ((ord(byts[3]) & 0b11) << 8) + ord(byts[2])

def bits_20_21(byts):
    """ Given at least a 3 byte value return the value of extracted bits 20 to 21
    """
    return (ord(byts[2]) & 0b110000) >> 4 

def bits_20_22(byts):
    """ Given at least a 3 byte value return the value of extracted bits 20 to 22
    """
    return (ord(byts[2]) & 0b1110000) >> 4 

def bits_20_23(byts):
    """ Given a 4 byte value return the value of extracted bits 20 to 23
    """
    return (ord(byts[2]) & 0b11110000) >> 4 

def bits_20_24(byts):
    """ Given at least a 4 byte value return the value of extracted bits 20 to 24
        In this case the extracted bits crosses a byte boundaries
    """
    return ((ord(byts[3]) & 0b1) << 4) + (( ord(byts[2]) & 0b11110000 ) >> 4 ) 

def bits_20_25(byts):
    """ Given at least a 4 byte value return the value of extracted bits 20 to 25
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[3]) & 0b11) << 4 ) + ( ( ord(byts[2]) & 0b11110000 ) >> 4 ) 

def bits_20_26(byts):
    """ Given at least a 3 byte value return the value of extracted bits 20 to 26
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[3]) & 0b111) << 4 ) + ( ( ord(byts[2]) & 0b11110000 ) >> 4 )
    
def bits_20_27(byts):
    """ Given at least a 3 byte value return the value of extracted bits 20 to 27
        In this case the extracted bits crosses a byte boundaries
    """
    return ( (ord(byts[3]) & 0b1111) << 4 ) + ( ( ord(byts[2]) & 0b11110000 ) >> 4 )

def bits_21_22(byts):
    """ Given at least a 3 byte value return the value of extracted bits 21 to 22
    """
    return (ord(byts[2]) & 0b1100000) >> 5 
    
def bits_21_24(byts):
    """ Given at least a 4 byte value return the value of extracted bits 21 to 24
        In this case the extracted bits crosses a byte boundaries
    """
    return ((ord(byts[3]) & 0b1) << 3)  + ( ( ord(byts[2]) & 0b11100000 ) >> 5 )
    
def bits_22_25(byts):
    """ Given at least a 4 byte value return the value of extracted bits 20 to 25
        In this case the extracted bits crosses a byte boundaries
    """
    return  ((ord(byts[3]) & 0b11) << 2 ) + ( ( ord(byts[2]) & 0b11000000 ) >> 6 ) 

def bits_23_24(byts):
    """ Given at least a 4 byte value return the value of extracted bits 23 to 24
        In this case the extracted bits crosses a byte boundaries
    """
    return  ( ord(byts[3]) & 0b1 )  + ( ( ord(byts[2]) & 0b10000000 ) >> 7 ) 

def bits_24_25(byts):
    """ Given at least a 4 byte value return the value of extracted bits 24 to 25
    """
    return ord(byts[3]) & 0b11 

def bits_24_26(byts):
    """ Given at least a 4 byte value return the value of extracted bits 24 to 26
    """
    return ord(byts[3]) & 0b111 

def bits_24_27(byts):
    """ Given at least a 4 byte value return the value of extracted bits 24 to 27
    """
    return ord(byts[3]) & 0b1111

def bits_25_26(byts):
    """ Given at least a 4 byte value return the value of extracted bits 25 to 26
    """
    return ( ord(byts[3]) & 0b110 ) >> 1    
    
def bits_25_27(byts):
    """ Given at least a 4 byte value return the value of extracted bits 25 to 27
    """
    return ( ord(byts[3]) & 0b1110 ) >> 1    
    
def bits_27_28(byts):
    """ Given a 4t least a byte value return the value of extracted bits 27 to 28
    """
    return ( ord(byts[3]) & 0b11000 ) >> 3 
    
def bits_28_31(byts):
    """ Given at least a 4 byte value return the value of extracted bits 28 to 31
    """
    return ( ord(byts[3]) & 0b11110000 ) >> 4
    
    