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

from bit_extract import *

def decode(buf):
    """ Given a buffer decode as Thumb instruction and return an instruction dictionary.
        Thumb instructions are either 32-bit (4 byts) or 16-bit (2 byts).
        
        The following reference manual was used:
        
            ARM Architecture Reference Manual 
            ARMv7-A and ARMv7-R edition
            ARM DDI 0406C.b (ID072512)
    """
    if len(buf) < 2:
        return None
        
    byts = buf[:4]
        
    inst_dict = {
        "mnem"        : None,
        "group"       : None,
        "len"         : -1,
        "addr"        : -1,
        "s_ops"       : [],
        "d_ops"       : [],
        "cond"        : None
    }
    return thumb_instruction(byts, inst_dict)
    

def thumb_instruction(byts, inst_dict):
    """ A6.1 
    """
    op = bits_11_15(byts)
    if op == 29 or op == 30 or op == 31:
        if len(byts) < 4:
            return None
        inst_dict["len"] = 4
        return instruction_32_bit(byts, inst_dict)
        
    else:
        byts = byts[:2]
        inst_dict["len"] = 2
        return instruction_16_bit(byts, inst_dict)


###################### 16-BIT INSTRUCTIONS ###############################################
def instruction_16_bit(byts, inst_dict):
    """ A6.2 16-bit Thumb instruction encoding
    """
    if bits_14_15(byts) == 0:
        inst_dict["mnem"] = "A6.2.1 Shift (immediate), add, subtract, move, and compare"  
        return inst_dict
        
    op1 = bits_10_15(byts)
    if op1 == 16:
        inst_dict["mnem"] = "A6.2.2 Data-processing"
        return inst_dict
        
    elif op1 == 17:
        return i16_special_branch_exchange(byts, inst_dict)
        
    op2 = bits_11_15(byts)
    op3 = bits_12_15(byts)
    op4 = bits_13_15(byts)
    
    if op2 == 9:
        inst_dict["mnem"] = "A8.6.59 LDR (literal)"
        return inst_dict
    
    if op2 == 20:
        inst_dict["mnem"] = "A8.6.10 ADR"
        return inst_dict
    
    if op2 == 21:
        inst_dict["mnem"] = "A8.6.8 ADD (SP plus immediate)"
        return inst_dict
    
    if op2 == 24:
        inst_dict["mnem"] = "A8.6.189 STM / STMIA / STMEA"
        return inst_dict
    
    if op2 == 25:
        inst_dict["mnem"] = "A8.6.53 LDM / LDMIA / LDMFD"
        return inst_dict

    if op2 == 28:
        return i16_branch_t2(byts, inst_dict)

    if op3 == 11:
        inst_dict["mnem"] = "A6.2.5 Miscellaneous 16-bit instructions"
        return inst_dict
        
    if op3 == 13:
        return i16_conditional_branch_supervisor_call(byts, inst_dict)
        
    if op3 == 5 or op4 == 3 or op4 == 4:
        inst_dict["mnem"] = "A6.2.4vLoad/store single data item"
        return inst_dict
    
    inst_dict["mnem"] = "<UNKNOWN> 16-bit instruction"
    return inst_dict

def i16_conditional_branch_supervisor_call(byts, inst_dict):
    """ A6.2.6 Conditional branch, and Supervisor Call
    """
    op = bits_8_11(byts)
    if op == 15:
        inst_dict["mnem"] = "A8.6.218 SVC (previously SWI)"
        return inst_dict
        
    elif op == 14:
        inst_dict["mnem"] = "UNDEFINED 16-bit instruction"
        return inst_dict
        
    else:
        return i16_branch_t1(byts, inst_dict)
    

def i16_branch_t1(byts, inst_dict):
    """ A8.6.16 Branch causes a branch to a target address.
        Encoding T1 B<c> <label>
    """
    inst_dict["mnem"] = "b"
    c = condition(bits_8_11(byts))
    if c != "uncond":
        inst_dict["mnem"] += c    
    inst_dict["group"] = "jump"
    imm8 = bits_0_7(byts)
    if imm8 >> 7 == 0: 
        inst_dict["d_ops"].append(imm8 * 2) 
    else:
        inst_dict["d_ops"].append(twos_compliment(imm8, 8) * 2) 
    return inst_dict
    
    
def i16_branch_t2(byts, inst_dict):
    """ A8.6.16 Branch causes a branch to a target address.
        Encoding T2 B <label>
    """
    inst_dict["mnem"] = "b"
    inst_dict["group"] = "jump"
    imm11 = bits_0_10(byts)
    if imm11 >> 7 == 0:
        inst_dict["d_ops"].append(imm11 * 2) 
    else:
        inst_dict["d_ops"].append(twos_compliment(imm11, 11) * 2)
    return inst_dict


def i16_special_branch_exchange(byts, inst_dict):
    """ A6.2.3 Special data instructions and branch and exchange
    """
    op = bits_6_9(byts)
    if op == 0:
        inst_dict["mnem"] = "A8.6.6 ADD Low registers"
        return inst_dict
        
    elif op > 1 and op < 4:
        inst_dict["mnem"] = "A8.6.6 ADD High registers"
        return inst_dict
    
    elif op == 4:
        inst_dict["mnem"] = "UNPREDICTABLE - 16 bit special data instruction"
        return inst_dict
    
    elif op > 4 and op < 8:
        inst_dict["mnem"] = "A8.6.36 CMP (register)"
        return inst_dict    

    elif op == 8:
        inst_dict["mnem"] = "A8.6.97 MOV low registers"
        return inst_dict     

    elif op > 8 and op < 12:
        inst_dict["mnem"] = "A8.6.97 MOV high registers"
        return inst_dict    
    
    elif op > 11 and op < 14:
        inst_dict["mnem"] = "A8.6.25 BX"
        return inst_dict    
        
    else:
        return i16_blx_register(byts, inst_dict)    

def i16_blx_register(byts, inst_dict):
    """ A8.6.24 BLX (register)
        BLX<c> <Rm>
    """
    inst_dict["mnem"] = "blx"
    inst_dict["group"] = "jump"
    rm = "r" + str(bits_3_6(byts))
    inst_dict["s_ops"].append(rm)
    return inst_dict
        
###################### 32-BIT INSTRUCTIONS ###############################################  
def instruction_32_bit(byts, inst_dict):
    """ A6.3 32-bit Thumb instruction encoding
    """
    byts = byts[2:4] + byts[:2]
    op1 = bits_27_28(byts)
    if op1 == 1:
        if bits_25_26(byts) == 0:
            if bit_22(byts) == 0:
                inst_dict["mnem"] = "A6.3.5 Load/store multiple"
                return inst_dict
            else:
                inst_dict["mnem"] = "A6.3.6 Load/store dual, load/store exclusive, table branch"
                return inst_dict

        else:
            if bits_25_26(byts) == 1:
                inst_dict["mnem"] = "A6.3.11 Data-processing (shifted register)"
                return inst_dict
                            
            elif bit_26(byts) == 1:
                inst_dict["mnem"] = "A6.3.18 Coprocessor instructions"
                return inst_dict
    
    elif op1 == 2:
        op = bit_15(byts)
        if op == 1:
            return i32_branches(byts, inst_dict)

        else:
            if bit_25(byts) == 0:
                inst_dict["mnem"] = "A6.3.1 Data-processing (modified immediate)"
                return inst_dict
            
            else: 
                inst_dict["mnem"] = "A6.3.3 Data-processing (plain binary immediate)"
                return inst_dict
    
    elif op1 == 3:
        if bit_26(byts) == 1:
            inst_dict["mnem"] = "A6.3.18 Coprocessor instructions"
            return inst_dict
            
        op2_1 = bits_25_26(byts)
        if op2_1 == 0:
            op2_2 = bits_26_24(byts)
            if op2_2 == 0 and bit_4(byts) == 0:
                inst_dict["mnem"] = "A6.3.10 Store single data item"
                return inst_dict
            
            elif op2_2 == 1 and bit_4(byts) == 0:
                inst_dict["mnem"] = "A7.7 Advanced SIMD element or structure load/store instructions"
                return inst_dict
        
            op2_3 = bits_20_22(byts)
            if op2_3 == 1:
                inst_dict["mnem"] = "A6.3.9 Load byte, memory hints"
                return inst_dict
            
            elif op2_3 == 3:
                inst_dict["mnem"] = "A6.3.8 Load halfword, memory hints"
                return inst_dict
                
            elif op2_3 == 5:
                inst_dict["mnem"] = "A6.3.7 Load word"
                return inst_dict
                
            elif op2_3 == 7:
                inst_dict["mnem"] = "A6.3 32-bit Thumb instruction UNDEFINED"
                return inst_dict
        
        else:
            if bits_24_26(byts) == 2:
                inst_dict["mnem"] = "A6.3.12 Data-processing (register)"
                return inst_dict
                
            op2_4 = bits_23_26(byts)
            if op2_4 == 6:
                inst_dict["mnem"] = "A6.3.16 Multiply, multiply accumulate, and absolute difference"
                return inst_dict
            
            elif op2_4 == 7:
                inst_dict["mnem"] = "A6.3.17 Long multiply, long multiply accumulate, and divide"
                return inst_dict
    
    inst_dict["mnem"] = "<UNKNOWN> 32-bit instruction"
    return inst_dict

def i32_branches(byts, inst_dict):
    """ A6.3.4 Branches and miscellaneous control
    """
    op1 = bits_12_14(byts)
    if op1 == 0:
        inst_dict["mnem"] = "B6.1.9 SMC (previously SMI)"
        return inst_dict
        
    if op1 == 2:
        inst_dict["mnem"] = "Permanently UNDEFINED"
        return inst_dict   
    
    op1_1 = (bit_14(byts) << 1 ) + bit_12(byts)
    if op1_1 == 0:
        if bits_23_26(byts) == 7:
            op1_2 = bits_20_22(byts)
            if op1_2 == 0 or op1_2 ==1:
                inst_dict["mnem"] = "A6.3.4 MSR"
                return inst_dict
            
            elif op1_2 == 2:
                inst_dict["mnem"] = "A6.3.4 Change proc state"
                return inst_dict            

            elif op1_2 == 3:
                inst_dict["mnem"] = "A6.3.4 BXJ"
                return inst_dict
            
            elif op1_2 == 4:
                inst_dict["mnem"] = "A6.3.4 SUB, PC, LR"
                return inst_dict
            
            elif op1_2 == 5:
                inst_dict["mnem"] = "A6.3.4 MSR"
                return inst_dict
        
        else:
            inst_dict["mnem"] = "A8.6.16 B"
            return inst_dict
    
    if op1_1 == 1:
        inst_dict["mnem"] = "A8.6.16 B"
        return inst_dict
            
    if op1_1 == 2:
        inst_dict["mnem"] = "blx"
        return i32_bl_blx(byts, inst_dict)
        
    if op1_1 == 3:
        inst_dict["mnem"] = "bl"
        return i32_bl_blx(byts, inst_dict)

    inst_dict["mnem"] = "<UNKNOWN> 32-bit branch instruction"
    return inst_dict


def i32_bl_blx(byts, inst_dict):
    """ A8.6.23 BL, BLX (immediate)
            Branch with Link calls a subroutine at a PC-relative address.
            Branch with Link and Exchange Instruction Sets 
    """
    inst_dict["group"] = "jump"
    c = condition(bits_28_31(byts))
    if c != "uncond":
        inst_dict["mnem"] += c
    
    s = bit_26(byts)
    if not(bit_13(byts) ^ s):
        i1 = 1
    else:
        i1 = 0
        
    if not(bit_11(byts) ^ s):
        i2 = 1
    else:
        i2 = 0
        
    imm10 = bits_16_25(byts)
    imm11 = bits_0_11(byts)
    imm22 = (imm10 << 10) + imm11
    imm25 = (s << 25) + (i1 << 24) + (i2 << 23) + imm22
    if imm25 >> 25 == 0:
        inst_dict["d_ops"].append(imm25*2)
    else:
        inst_dict["d_ops"].append( twos_compliment(imm25, 25) * 2 )
    return inst_dict

def twos_compliment(val, bits_in_word):
    return val-(1<<bits_in_word)

def condition(byts): 
    """ A8.3
    """
    mnem = {
        0:"eq", # Equal: Z == 1
        1:"ne", # Not equal: Z == 0
        2:"cs", # Carry set: C == 1
        3:"cc", # carry clear C == 0
        4:"mi", # Minus, negative: N == 1
        5:"pl", # Plus: N == 0
        6:"vs", # Overflow: V == 1
        7:"vc", # No overflow: V == 0
        8:"hi", # Unsigned higher: C == 1 and Z == 0
        9:"ls", # Unsigned lower: C == 0 and Z == 1
        10:"ge", # Signed greater: than or equal N == V
        11:"lt", # Signed less than: N != V
        12:"gt", # Signed greater than: Z == 0 and N = V
        13:"le", # Signed less than or equal: Z == 1 or N != V
        14:"al", # Always (unconditional): Any
        15:"uncond", # Always (unconditional)
    }
    return mnem[byts]
    
        
######### MAIN FOR TESTING ###############################################################
if __name__ == "__main__":
    instrs0 = [
        (0x817C, "\x00\xE0", "b <0x8180>"),
        (0x818A, "\x00\xE0", "b <0x818E>"),
        (0x8198, "\x00\xE0", "b <0x819C>"),
        (0x83BC, "\x0A\xE0", "b <0x83D4>"),
        (0x8426, "\xEB\xE7", "b <0x8400>"),
        (0x85D4, "\x89\xE7", "b <0x84EA>"),
        (0x8426, "\xEB\xE7", "b <0x8400>"),    

    ]
    
    instrs1 = [
        (0x8340, "\xF7\xD1", "bne <0x8332>"),
        (0x83DE, "\x24\xD0", "beq <0x83DA>"),
        (0x83F6, "\x01\xD1", "bne <0x83FC>"),
        (0x8418, "\x04\xD1", "bne <0x8424>"),
        (0x8460, "\x00\xD1", "bne <0x8464>"),
        (0x846E, "\x09\xD1", "bne <0x8484>"),
        (0x8478, "\x04\xD0", "beq <0x8484>"),
        (0x84A2, "\xF8\xD0", "beq <0x8496>"),
        (0x84BC, "\x00\xD1", "bne <0x84c0>"),    
        (0x8616, "\x00\xDD", "ble <0x861A>"),
        (0x8628, "\x10\xDD", "bne <0x864A>"),
        (0x865E, "\x0C\xDC", "bgt <0x867A>"),  
    ]
    
    instrs2 = [
        (0x817E, "\x98\x47", "blx r3"),
        (0x86DE, "\x88\x47", "blx r1"),
    
    ]

    instrs3 = [
        (0x851C, "\x02\xF0\x7A\xFA", "bl <0xAA14>"),
        (0x8558, "\x02\xF0\x5A\xEE", "blx <0xB210>"),
        (0x857C, "\x02\xF0\x48\xEE", "blx <0xB210>"),
        (0x858A, "\x03\xF0\xB1\xF8", "bl <0xB6F0>"), 
        (0x85F4, "\x00\xF0\xB6\xFA", "bl <0x8B04>"), 
        (0x8666, "\x02\xF0\xD4\xED", "blx <0xB210>"),
        (0x8688, "\x03\xF0\x32\xF8", "bl <0xB6F0>"),
    ]
    
    instrs = []
    instrs.extend(instrs0)
    instrs.extend(instrs1)
    instrs.extend(instrs2)
    instrs.extend(instrs3)


    for i in instrs:
        print "-"*95
        offset = i[0]
        byts = i[1]
        desc = i[2]
        
        x = decode(offset, byts)
        m = x["mnem"]
        s = ",".join(x["s_ops"])
        d = ",".join(x["d_ops"])
        a = x["addr"] 
        c = x["cond"]
        l = x["len"]
        
        print " %s --> offset:%s mnem:%s  addr:%s  src:%s  dst:%s  len:%s" % (desc, hex(offset), m, hex(a), s, d, l)
    print "-"*95

