###################### UNCLASSIFIED // OFFICIAL USE ONLY #################################
from bit_extract import *

def decode(buf):
    """ Given a buffer decode as ARM instruction and return an instruction dictionary.
        ARM instructions are always 32 bits (4 bytes).
        
        The following reference manual was used:
        
            ARM Architecture Reference Manual 
            ARMv7-A and ARMv7-R edition
            ARM DDI 0406C.b (ID072512)
    """
    if len(buf) < 4: return None
    byts = buf[:4]
    
    inst_dict = {
        "mnem"        : None,
        "group"       : None, 
        "len"         : 4,
        "addr"        : -1,
        "s_ops"       : [],
        # 'd_op': {'subtype': 'near', 'type': 'rel', 'data': 320729}
        # 'd_op': {'type': 'eff_addr', 'data': {'disp': 4764964, 'base': None, 'scale': 1, 'idx': None}}
        # 'd_op': {'type': 'imm', 'data': 12}
        "d_op"       : {},  
        "cond"        : None
    }
    inst_dict = arm_instruction(byts, inst_dict)
    return inst_dict
    
    
def arm_instruction(byts, inst_dict):
    """ A5.1 Highest level class of instructions
    """
    inst_dict["cond"] = condition(byts)
    if bits_28_31(byts) == 15:
        return unconditional_inst(byts, inst_dict)
    
    op1 = bits_25_27(byts)
    if op1 == 0 or op1 == 1:
        return data_processing_inst(byts, inst_dict)
    
    elif op1 == 2:
        return load_store_inst(byts, inst_dict)
        
    elif op1 == 3 and bit_4(byts) == 1:
        return media_inst(byts, inst_dict)
        
    elif op1 == 3:
        return load_store_inst(byts, inst_dict)
    
    elif op1 == 4 or op1 == 5:
        return branch_block_inst(byts, inst_dict)
        
    elif op1 == 6 or op1 == 7:
        return supervisor_inst(byts, inst_dict)
        
    else:
        return inst_dict


######### CONDITIONAL FIELD ##############################################################
def is_unconditional(byts):
    return bits_28_31(byts) == 15
    
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
    return mnem[bits_28_31(byts)]
    
        
######### BRANCH, BRANCH WITH LINK, AND BLOCK DATA TRANSFER ##############################
def branch_block_inst(byts, inst_dict):
    """ A5.5
        Using the 6 bit op field determine what type of branch or block instruction
    """
    # First check the 4 most significan bits added to the least most while ignoring the x bit
    op1 = (bits_22_25(byts) << 1 ) + bit_20(byts) # 0b????x?
    op = bits_20_25(byts)
    c = condition(byts)
    if c == "al": c = ""
        
    if op1 == 0: # 0b0000x0
        """ A8.6.190 Store Multiple Decrement After
            STMDA<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "stmda" + c
        inst_dict["group"] = "stack"
        return store_multiple_operands(byts, inst_dict)
    
    elif op1 == 1: # 0b0000x1 
        """ A8.6.54 Load Multiple Decrement After
            LDMDA<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "ldmda" + c
        inst_dict["group"] = "stack"
        return load_multiple_operands(byts, inst_dict)

    elif op1 == 4: # 0b0010x0
        """ A8.6.189 Store Multiple (Increment After) 
            STM<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "stm" + c
        inst_dict["group"] = "stack"
        return store_multiple_operands(byts, inst_dict)

    elif op1 == 5: # 0b0010x1 
        if bits_16_19(byts) == 13: # rn
            """ A8.8.132 Pop Multiple Registers 
            """
            inst_dict["mnem"] = "pop"
            inst_dict["group"] = "stack"
            return load_multiple_operands(byts, inst_dict)
            
        else:
            """ A8.6.53 Load Multiple (Increment After)
                LDM<c> <Rn>{!},<registers>
            """
            inst_dict["mnem"] = "ldm" + c
            inst_dict["group"] = "stack"
            return load_multiple_operands(byts, inst_dict)

    elif op1 == 8: # 0b0100x0
        if bits_16_19(byts) == 13: # rn
            """ A8.8.133 Push Multiple Registers
            """
            inst_dict["mnem"] = "push"
            inst_dict["group"] = "stack"
            return store_multiple_operands(byts, inst_dict)
            
        else:
            """ A8.6.191 Store Multiple Decrement Before
                STMDB<c> <Rn>{!},<registers>
            """
            inst_dict["mnem"] = "stmdb" + c
            inst_dict["group"] = "stack"
            return store_multiple_operands(byts, inst_dict)

    elif op1 == 9: # 0b0100x1
        """ A8.6.55 Load Multiple Decrement Before
            LDMDB<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "ldm" + c
        inst_dict["group"] = "stack"
        return load_multiple_operands(byts, inst_dict)

    elif op1 == 12: # 0b0110x0
        """ A8.6.192 Store Multiple Increment Before
            STMIB<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "stmib" + c
        inst_dict["group"] = "stack"
        return store_multiple_operands(byts, inst_dict)
        
    elif op1 == 13: # 0b0110x1
        """ A8.6.56 Load Multiple Increment Before
            LDMIB<c> <Rn>{!},<registers>
        """
        inst_dict["mnem"] = "ldmib" + c
        inst_dict["group"] = "stack"
        return load_multiple_operands(byts, inst_dict)
    
    # Next check the bits 25+22+20
    op2 = (bit_25(byts) << 2 ) + ( bit_22(byts) << 1 ) + bit_20(byts)
    if op2 == 2: # 0b0xx1x0
        """ B6.1.11 Store Multiple (user registers)
            STM{amode}<c><q> <Rn>, <registers>^
        """
        amode = get_amode(bits_23_24(byts))
        inst_dict["mnem"] = "stm" + "{" + amode + "}" + c
        inst_dict["group"] = "stack"
        return store_multiple_operands(byts, inst_dict)

    elif op2 == 3: # 0b0xx1x1
        """ B6.1.3 Load Multiple (user registers)
            LDM{<amode>}<c><q> <Rn>, <registers_without_pc>^
        
            B6.1.2 Load Multiple (exception return) if bit_15 == 1
            LDM{<amode>}<c> <Rn>{!},<registers_with_pc>^
        """
        amode = get_amode(bits_23_24(byts))
        inst_dict["mnem"] = "ldm" + "{" + amode + "}" + c
        inst_dict["group"] = "exec"
        return load_multiple_operands(byts, inst_dict)
    
    #  Last check bits 24+25
    op3 = bits_24_25(byts)
    if op3 == 2: # 0b10xxxx
        """ A8.6.16 Branch
            B<c> <label
        """
        inst_dict["mnem"] = "b" + c
        inst_dict["group"] = "exec"
        imm24 = hex(bits_0_23(byts))
        s_op = {'type': 'imm', 'data': imm24} 
        inst_dict["s_ops"].append(s_op)
        return inst_dict
    
    elif op3 == 3: # 0b11xxxx
        """ A8.6.23 Branch with Link
            BL<c> <label>
              or 
            BLX <label> if bits 28-31 == 0b1111
            
            A8.6.25 BX
        """
        
        if bits_28_31(byts) != 15:
            inst_dict["mnem"] = "bl" + c
        else:
            inst_dict["mnem"] = "blx"
        inst_dict["group"] = "exec"
        imm24 = hex(bits_0_23(byts))
        s_op = {'type': 'imm', 'data': imm24}
        inst_dict["s_ops"].append(s_op)
        return inst_dict
    
    inst_dict["mnem"] = "<UNKNOWN>"
    inst_dict["group"] = "invalid"    
    return inst_dict   


def store_multiple_operands(byts, inst_dict):
    """ Helper function for store multiple instructions
    """
    rn = "r%s" % bits_16_19(byts)
    rl = get_reg_list(byts)
    w = bit_21(byts)
    if w == 1:
        rn += "!"
    s_op = {'type': 'imm', 'data': rn}
    d_op = {'type': 'imm', 'data': rl}
    inst_dict["s_ops"].append(s_op)
    inst_dict["d_op"] = d_op
    return inst_dict


def load_multiple_operands(byts, inst_dict):
    """ Helper function for load multiple instructions
    """
    rn = "r%s" % bits_16_19(byts)
    rl = get_reg_list(byts)
    w = bit_21(byts)
    if w == 1:
        rn += "!"
    s_op = {'type': 'imm', 'data': rl}
    d_op = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op)
    inst_dict["d_op"] = d_op
    return inst_dict
    

######### DATA PROCESSING AND MISC #######################################################
def data_processing_inst(byts, inst_dict):
    """ A5.2
    """ 
    if bit_25(byts) == 0:
        op1_1 = (bit_24(byts) << 2) + (bit_23(byts) << 1) + bit_20(byts) # op1 ??xx?    
        if op1_1 != 4:
            if bit_4(byts) == 0:
                return data_processing_register(byts, inst_dict) # A5.2.1
                 
            elif bit_7(byts) == 0 and bit_4(byts) == 1:
                return data_processing_register_shifted(byts, inst_dict) # A5.2.2
                
        elif op1_1 == 4:
            if bit_7(byts) == 0:
                return data_processing_misc(byts, inst_dict) # A5.2.12
                
            elif bit_7 == 1 and bit_4 ==0:
                return data_processing_halfword_multiply(byts, inst_dict) # A5.2.7
                
        op2 = bits_4_7(byts)
        op2_1 = (bits_6_7(byts) << 1 ) + bit_4(byts)
        op1_2 = (bit_24(byts) << 1) + bit_21(byts)
        if op1_2 != 1:
            if op2 == 11 or op2_1 == 7:
                return data_processing_extra_load_store(byts, inst_dict) # A5.2.28
            
        elif op1_2 == 1:
            if op2 == 11:
                return data_processing_extra_load_store_unpriv(byts, inst_dict) # A5.2.9
                
            elif op2_1 == 7:            
                return data_processing_extra_load_store(byts, inst_dict) # A5.2.28
                
        if bit_24(byts) == 0:
            return data_processing_multiply_accumulate(byts, inst_dict) # 5.2.5
        
        else: # bit 24 == 1
            return data_processing_synchronization_primitives(byts, inst_dict) # A5.2.10
            
    else: # bit_25 == 1
        op1_3 = (bit_24(byts) << 2) + (bit_23(byts) << 1) + bit_20(byts)
        if op1_3 != 4:
            return data_processing_immediate(byts, inst_dict) # A5.2.3
        
        op1 = bits_20_24(byts)
        if op1 == 16: 
            return move_immediate_inst(byts, inst_dict) # A8.8.102
            
        if op1 == 20:
            return mov_top_inst(byts, inst_dict) # A8.8.106
            
        if op1 == 18 or op1 == 20:
            return msr_immediate(byts, inst_dict) 
    
    inst_dict["group"] = "invalid" 
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict


def mov_top_inst(byts, inst_dict):
    """ Move Top A8.8.106
        MOVT<c> <Rd>, #<imm16>
    """
    c = condition(byts)
    if c == "al": c = ""
    
    inst_dict["mnem"] = "movt" + c
    inst_dict["group"] = "load"
    
    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    s_op = {'type': 'imm', 'data': imm16(byts)}
    inst_dict["s_ops"].append(s_op)

    return inst_dict
    
    
def move_immediate_inst(byts, inst_dict):
    """ Move (immediate) A8.8.102
        MOV{S}<c> <Rd>, #<const>
        MOVW<c> <Rd>, #<imm16>
    """
    c = condition(byts)
    if c == "al": c = ""
    
    inst_dict["mnem"] = "mov" 
    inst_dict["group"] = "load"
    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op
    imm4 = bits_16_19(byts)
    if imm4 == 0: # MOV{S}<c> <Rd>, #<const>
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s"
            s_op = {'type': 'imm', 'data': imm12(byts)}
            inst_dict["s_ops"].append(s_op)
        
    else: # MOVW<c> <Rd>, #<imm16>
        inst_dict["mnem"] += "w"
        s_op = {'type': 'imm', 'data': imm16(byts)}
        inst_dict["s_ops"].append(imm16)
        
    inst_dict["mnem"] += c
    return inst_dict
    
    
def data_processing_synchronization_primitives(byts, inst_dict):
    """ A5.2.10
    """
    op = bits_20_23(byts)
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["group"] = "load"
    
    if op == 0 or op == 4:
        """ Swap A8.8.229
            SWP{B}<c> <Rt>, <Rt2>, [<Rn>]
        """
        inst_dict["mnem"] = "swp"
        if bit_22(byts) == 1:
            inst_dict["mnem"] += "b"
        inst_dict["mnem"] += c
        return synchronization_primitives_3_operands(byts, inst_dict)
            
    elif op == 8:
        """ Store Register Exclusive A8.8.212 
            STREX<c> <Rd>, <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "strex" + c
        return synchronization_primitives_3_operands(byts, inst_dict)
        
    elif op == 9:
        """ Load Register Exclusive A8.8.75
            LDREX<c> <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "ldrex" + c
        return synchronization_primitives_2_operands(byts, inst_dict)
        
    elif op == 10:
        """ Store Register Exclusive Doubleword A8.8.214
            STREXD<c> <Rd>, <Rt>, <Rt2>, [<Rn>]
        """
        inst_dict["mnem"] = "strexd" + c
        return synchronization_primitives_3_operands(byts, inst_dict)
        
    elif op == 11:
        """ Load Register Exclusive Doubleword A8.8.77
            LDREXD<c> <Rt>, <Rt2>, [<Rn>]
        """
        inst_dict["mnem"] = "ldrexd" + c
        return synchronization_primitives_3_operands(byts, inst_dict)
        
    elif op == 12:
        """ Store Register Exclusive Byte A8.8.213
            STREXB<c> <Rd>, <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "strexb" + c
        return synchronization_primitives_3_operands(byts, inst_dict)
        
    elif op == 13:
        """ Load Register Exclusive Byte A8.8.76
            LDREXB<c> <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "ldrexb" + c
        return synchronization_primitives_2_operands(byts, inst_dict)
        
    elif op == 14:
        """ Store Register Exclusive Halfword A8.8.215
            STREXH<c> <Rd>, <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "strexh" + c
        return synchronization_primitives_3_operands(byts, inst_dict)       
        
    elif op == 15:
        """ Load Register Exclusive Halfword A8.8.78
            LDREXH<c> <Rt>, [<Rn>]
        """
        inst_dict["mnem"] = "ldrexh" + c
        return synchronization_primitives_2_operands(byts, inst_dict)
    
    inst_dict["group"] = "invalid" 
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict
   
   
def synchronization_primitives_3_operands(byts, inst_dict):
    """ Helper function for synchronization primitives instructions
        MNEM<c> <Rt>, <Rd>, [<Rn>]
    """
    rt = "r%s"   % str(bits_0_3(byts))
    rd = "r%s"   % str(bits_12_15(byts))
    rn = "[r%s]" % str(bits_16_19(byts))

    s_op1 = {'type': 'imm', 'data': rd}
    s_op2 = {'type': 'imm', 'data': rn}
    
    inst_dict["s_ops"].append(s_op1)
    inst_dict["s_ops"].append(s_op2)

    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op

    return inst_dict


def synchronization_primitives_2_operands(byts, inst_dict):
    """ Helper function for synchronization primitives instructions
        MNEM<c> <Rt>, [<Rn>]
    """    
    rn = "[r%s]" % str(bits_16_19(byts))
    s_op = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op)

    rt = "r%s" % str(bits_12_15(byts))
    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op

    return inst_dict
        
        
def data_processing_multiply_accumulate(byts, inst_dict):
    """ 5.2.5
    """
    op = bits_20_23(byts)
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["group"] = "arith" 

    if op == 0 or op == 1:
        """ Multiply A8.8.114
            MUL{S}<c> <Rd>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "mul"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c
        return mul_accumulate_inst_3_operands(byts, inst_dict)
    
    elif op == 2 or op == 3:
        """ Multiply Accumulate A8.8.100
            MLA{S}<c> <Rd>, <Rn>, <Rm>, <Ra>
        """    
        inst_dict["mnem"] = "mla" 
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c
        inst_dict = mul_accumulate_inst_4_operands(byts, inst_dict)
        return inst_dict
            
    elif op == 4:
        """ Unsigned Multiply Accumulate Accumulate Long A8.8.255
            UMAAL<c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "umall" + c
        return mul_accumulate_inst_split_4_operands(byts, inst_dict)
        
    elif op == 6:
        """ Multiply and Subtract A8.8.101
            MLS<c> <Rd>, <Rn>, <Rm>, <Ra>
        """ 
        inst_dict["mnem"] = "mls" + c
        return mul_accumulate_inst_4_operands(byts, inst_dict)
        
    elif op == 8 or op == 9:
        """ Unsigned Multiply Long A8.8.257
            UMULL{S}<c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "umull"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c
        return mul_accumulate_inst_split_4_operands(byts, inst_dict)
        
    elif op == 10 or op == 11:
        """ Unsigned Multiply Accumulate Long A8.8.256
            UMLAL{S}<c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "umlal"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c
        return mul_accumulate_inst_split_4_operands(byts, inst_dict)
        
    elif op == 12 or op == 13:
        """ Signed Multiply Long A8.8.189
            SMULL{S}<c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "smull"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c
        return mul_accumulate_inst_split_4_operands(byts, inst_dict)
        
    elif op == 14 or op == 15:
        """ Signed Multiply Accumulate Long A8.8.178
            SMLAL{S}<c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "smlal"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s" 
        inst_dict["mnem"] += c

        return mul_accumulate_inst_split_4_operands(byts, inst_dict)       
    
    inst_dict["group"] = "invalid" 
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict
    
    
def mul_accumulate_inst_3_operands(byts, inst_dict):
    """ Helper function for multiply_accumulate instructions
        MNEM <Rd>, <Rn>, <Rm>
    """
    rn = "r%s" % bits_0_3(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s" % bits_8_11(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    rd = "r%s" % bits_16_19(byts)    
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op 

    return inst_dict
        

def mul_accumulate_inst_4_operands(byts, inst_dict):
    """ Helper function for multiply_accumulate instructions
        MNEM <Rd>, <Rn>, <Rm>, <Ra>
    """
    rn = "r%s" % bits_0_3(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s" % bits_8_11(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    ra = "r%s" % bits_12_15(byts)
    s_op3 = {'type': 'imm', 'data': ra}
    inst_dict["s_ops"].append(s_op3)

    rd = "r%s" % bits_16_19(byts)    
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op 

    return inst_dict


def mul_accumulate_inst_split_4_operands(byts, inst_dict):
    """ Helper function for multiply_accumulate instructions
        MNEM <RdHi>, <RdLo>, <Rn>, <Rm>
    """
    rn = "r%s" % bits_0_3(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s" % bits_8_11(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    rd_low = "r%s" % bits_12_15(byts)
    rd_high = "r%s" % bits_16_19(byts)
    rd = "{%s,%s}" % (rd_high, rd_low)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op 

    return inst_dict

    
def data_processing_extra_load_store_unpriv(byts, inst_dict):
    """ A5.2.9
    """
    op2 = bits_5_6(byts)
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["group"] = "load"
    
    if op2 == 1:
        if bit_20(byts) == 0:
            """ Store Register Halfword Unprivileged A8.8.219
            """
            inst_dict["mnem"] = "strht" + c
            return extra_load_store_unpriv_inst(byts, inst_dict)
            
        else: # bit 20 == 1
            """ Load Register Halfword Unprivileged A8.8.83
            """
            inst_dict["mnem"] = "ldrht" + c
            return extra_load_store_unpriv_inst(byts, inst_dict)
    
    elif op2 == 2 and bit_20(byts) == 1:
        """ Load Register Signed Byte Unprivileged A8.8.87
        """
        inst_dict["mnem"] = "ldrsbt" + c
        return extra_load_store_unpriv_inst(byts, inst_dict)
              
    elif op2 == 3 and bit_20(byts) == 1:
        """ Load Register Signed Halfword Unprivileged A8.8.91
        """
        inst_dict["mnem"] = "ldrsht" + c
        return extra_load_store_unpriv_inst(byts, inst_dict)
    
    inst_dict["group"] = "invalid" 
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict


def extra_load_store_unpriv_inst(byts, inst_dict):
    """ Helper function for extra load store unpriv operands
        MNEM<c> <Rt>, [<Rn>] {, #+/-<imm8>}
        MNEM<c> <Rt>, [<Rn>], +/-<Rm>
    """
    rt = "r%s" % bits_12_15(byts)
    rn = "[r%s]" % bits_16_19(byts)

    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op
    
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)
    
    imm4H = bits_8_11(byts)
    if imm4H == 0:
        rm = "r%s" %  bits_0_3(byts)
        s_op2 = {'type': 'imm', 'data': rm}
        inst_dict["s_ops"].append(s_op2)

    else:
        imm8 = "#{%s}" % hex((imm4H << 4 ) + bits_0_3(byts))
        s_op2 = {'type': 'imm', 'data': imm8}
        inst_dict["s_ops"].append(s_op2)
        
    return inst_dict
    

def data_processing_halfword_multiply(byts, inst_dict):
    """ A5.2.7
    """
    op1 = bits_21_22(byts)
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["group"] = "arith"
    
    if op1 == 0:
        """ Signed Multiply Accumulate (halfwords) A8.8.176
            SMLA<x><y><c> <Rd>, <Rn>, <Rm>, <Ra>
        """
        inst_dict["mnem"] = "smla" 
        inst_dict["mnem"] += c
        inst_dict = halfword_multiply_inst(byts, inst_dict)

        return inst_dict
        
    elif op1 == 1:
        if bit_5(byts) == 0:
            """ Signed Multiply Accumulate (word by halfword) A8.8.181
                SMLAW<y><c> <Rd>, <Rn>, <Rm>, <Ra>
            """
            inst_dict["mnem"] = "smlaw" 
            inst_dict["mnem"] += c
            inst_dict = halfword_multiply_inst(byts, inst_dict)
            return inst_dict
        
        else: # bit 5 == 1
            """ Signed Multiply (word by halfword) A8.8.190
                SMULW<y><c> <Rd>, <Rn>, <Rm>
            """
            inst_dict["mnem"] = "smulw" 
            inst_dict["mnem"] += c
            inst_dict = halfword_multiply_inst(byts, inst_dict)
            return inst_dict
    
    elif op1 == 2:
        """ Signed Multiply Accumulate Long (halfwords) A8.8.179
            SMLAL<x><y><c> <RdLo>, <RdHi>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "smulw"
        inst_dict["mnem"] += c

        rd_low  = "#%s" % bits_12_15(byts)
        rd_high = "#%s" % bits_16_19(byts)
        rd = "{r%s,r%s}" % (rd_low, rd_high)
        d_op = {'type': 'imm', 'data': rd}
        inst_dict["d_op"] = d_op

        rn = "r%s" % bits_0_3(byts)
        s_op1 = {'type': 'imm', 'data': rn}
        inst_dict["s_ops"].append(s_op1)
        
        rm = "r%s" % bits_8_11(byts)
        s_op2 = {'type': 'imm', 'data': rm}
        inst_dict["s_ops"].append(s_op2)
        
        return inst_dict
    
    else: # op1 == 3
        """ Signed Multiply (halfwords) A8.8.188
            SMUL<x><y><c> <Rd>, <Rn>, <Rm>
        """
        inst_dict["mnem"] = "smul"
        return halfword_multiply_inst(byts, inst_dict)


def halfword_multiply_inst(byts, inst_dict):
    """ Helper function for halfword multiply instructions
    """
    rn = "r%s" % bits_0_3(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(rn)
    
    rm = "r%s" % bits_8_11(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(rm)
    
    rd = "r%s" % bits_16_19(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    return inst_dict


def data_processing_extra_load_store(byts, inst_dict):
    """ A5.2.28
    """
    op2 = bits_5_6(byts)
    op1_1 = (bit_22(byts) << 1) + bit_20(byts) # 0bxx?x?
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["group"] = "load"
    
    if op2 == 1:
        if op1_1 == 0:
            """ Store Register Halfword (register) A8.8.218
            """
            inst_dict["mnem"] = "strh" + c
            return data_processing_extra_load_store_reg_ops(byts, inst_dict)
        
        elif op1_1 == 1:
            """ Load Register Halfword (register) A8.8.82
            """
            inst_dict["mnem"] = "ldrh" + c
            return data_processing_extra_load_store_reg_ops(byts, inst_dict)
        
        elif op1_1 == 2:
            """ Store Register Halfword (immediate) A8.8.217
            """
            inst_dict["mnem"] = "strh" + c
            return data_processing_extra_load_store_reg_imm_ops(byts, inst_dict)
        
        elif op1_1 == 3:
            if bits_16_19(byts) != 15:
                """ Load Register Halfword (immediate) A8.8.80
                """
                inst_dict["mnem"] = "ldrh" + c
                return data_processing_extra_load_store_reg_imm_ops(byts, inst_dict)
            
            else:        
                """ Load Register Halfword (literal) A8.8.81
                """
                inst_dict["mnem"] = "ldrh" + c
                return data_processing_extra_load_store_reg_lit_ops(byts, inst_dict)
    
    elif op2 == 2:
        if op1_1 == 0:
            """ Load Dual Register (register) A8.8.74
            """
            inst_dict["mnem"] = "ldrd" + c
            return data_processing_extra_load_store_dual_reg_ops(byts, inst_dict)
            
        elif op1_1 == 1:
            """ Load Register Signed Byte (register) A8.8.86
            """
            inst_dict["mnem"] = "ldrsb" + c
            return data_processing_extra_load_store_reg_ops(byts, inst_dict)
        
        elif op1_1 == 2:
            if bits_16_19(byts) != 15:
                """ Load Register Dual (immediate) A8.8.72
                """
                inst_dict["mnem"] = "ldrd" + c
                return data_processing_extra_load_store_dual_reg_imm_ops(byts, inst_dict)
            
            else:   
                """ Load Register Dual (literal) A8.8.73
                    LDRD<c> <Rt>, <Rt2>, <label> 
                    LDRD<c> <Rt>, <Rt2>, [PC, #-0]
                """
                inst_dict["mnem"] = "ldrd" + c
                return data_processing_extra_load_store_dual_reg_lit_ops(byts, inst_dict)
        
        elif op1_1 == 3:
            if bits_16_19(byts) != 15:
                """ Load Register Signed Byte (immediate) A8.8.84
                """
                inst_dict["mnem"] = "ldrsb" + c
                return data_processing_extra_load_store_reg_imm_ops(byts, inst_dict)
            
            else:   
                """ Load Register Signed Byte (literal) A8.8.85
                """
                inst_dict["mnem"] = "ldrsb" + c
                return data_processing_extra_load_store_reg_lit_ops(byts, inst_dict)

    
    elif op2 == 3:
        if op1_1 == 0:
            """ Store Register Dual (register) A8.8.211
            """
            inst_dict["mnem"] = "strd" + c
            return data_processing_extra_load_store_dual_reg_ops(byts, inst_dict)
        
        elif op1_1 == 1:
            """ Load Register Signed Halfword (register) A8.8.90
            """
            inst_dict["mnem"] = "ldrsh" + c
            return data_processing_extra_load_store_reg_ops(byts, inst_dict)
        
        elif op1_1 == 2:
            """ Store Register Dual (immediate) A8.8.210
            """
            inst_dict["mnem"] = "strd" + c
            return data_processing_extra_load_store_dual_reg_imm_ops(byts, inst_dict)
        
        elif op1_1 == 3:
            if bits_16_19(byts) != 15:
                """ Load Register Signed Halfword (immediate) A8.8.88
                """
                inst_dict["mnem"] = "ldrsh" + c
                return data_processing_extra_load_store_reg_imm_ops(byts, inst_dict)
            
            else:  
                """ Load Register Signed Halfword (literal) A8.8.89
                """
                inst_dict["mnem"] = "ldrsh" + c
                return data_processing_extra_load_store_reg_lit_ops(byts, inst_dict)
                
    inst_dict["group"] = "invalid"
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict


def data_processing_extra_load_store_reg_ops(byts, inst_dict):
    """ MNEM<c> <Rt>, [<Rn>,+/-<Rm>]{!} # T,T
        MNEM<c> <Rt>, [<Rn>],+/-<Rm>    # F,T
    """
    rt = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op

    rn = "[r%s]" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "[r%s]" % bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)


def data_processing_extra_load_store_reg_imm_ops(byts, inst_dict):
    """ MNEM<c> <Rt>, [<Rn>{, #+/-<imm8>}]  # T,F
        MNEM<c> <Rt>, [<Rn>], #+/-<imm8>    # T,T
        MNEM<c> <Rt>, [<Rn>, #+/-<imm8>]!   # F,T
    """
    rt = "r" + str(bits_12_15(byts))
    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op
    

    rn = "[r]" + str(bits_16_19(byts))
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    imm8 = "#" + hex( (bits_8_11(byts) << 4) + bits_0_3(byts) )
    s_op2 = {'type': 'imm', 'data': imm8}
    inst_dict["s_ops"].append(s_op2)

    return inst_dict


def data_processing_extra_load_store_reg_lit_ops(byts, inst_dict):
    """ MNEM<c> <Rt>, <label> 
        MNEM<c> <Rt>, [PC, #-0] Special case
    """
    rt = "r" + str(bits_12_15(byts))
    d_op = {'type': 'imm', 'data': rt}
    inst_dict["d_op"] = d_op
    
    imm8 = "#" + hex( (bits_8_11(byts) << 4) + bits_0_3(byts) )
    s_op = {'type': 'imm', 'data': imm8}
    inst_dict["s_ops"].append(s_op)

    return inst_dict


def data_processing_extra_load_store_dual_reg_ops(byts, inst_dict):
    """ MNEM{<c>}{<q>} <Rt>, <Rt2>, [<Rn>, +/-<Rm>] # T,F
        MNEM<c> <Rt>, <Rt2>, [<Rn>,+/-<Rm>]{!}      # T,T
        MNEM<c> <Rt>, <Rt2>, [<Rn>],+/-<Rm>         # F,T
    """
    rt = bits_12_15(byts)
    rtt = "{r%s,r%s" % (rt, rt+1)
    d_op = {'type': 'imm', 'data': rtt}
    inst_dict["d_op"] = d_op

    rn = "[r%s]" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r" + str(bits_0_3(byts))
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)
 
    return inst_dict


def data_processing_extra_load_store_dual_reg_imm_ops(byts, inst_dict):
    """ MNEM<c> <Rt>, <Rt2>, [<Rn>{, #+/-<imm8>}] # T,F
        MNEM<c> <Rt>, <Rt2>, [<Rn>], #+/-<imm8>   # T,T
        MNEM<c> <Rt>, <Rt2>, [<Rn>, #+/-<imm8>]!  # F,T
    """
    rt = bits_12_15(byts)
    rtt = "{r%s,r%s" % (rt, rt+1)
    d_op = {'type': 'imm', 'data': rtt}
    inst_dict["d_op"] = d_op

    rn = "[r%s]" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    imm8 = "#" + hex( (bits_8_11(byts) << 4) + bits_0_3(byts) )
    s_op2 = {'type': 'imm', 'data': imm8}
    inst_dict["s_ops"].append(s_op2)
    
    return inst_dict


def data_processing_extra_load_store_dual_reg_lit_ops(byts, inst_dict):
    """ MNEM<c> <Rt>, <Rt2>, <label> 
        MNEM<c> <Rt>, <Rt2>, [PC, #-0]
    """
    rt = bits_12_15(byts)
    rtt = "{r%s,r%s" % (rt, rt+1)
    d_op = {'type': 'imm', 'data': rtt}
    inst_dict["d_op"] = d_op

    imm8 = "#" + hex( (bits_8_11(byts) << 4) + bits_0_3(byts) )
    s_op2 = {'type': 'imm', 'data': imm8}
    inst_dict["s_ops"].append(s_op2)

    return inst_dict


def data_processing_misc(byts, inst_dict):
    """ A5.2.12
    """
    op2 = bits_4_6(byts)
    op = bits_21_22(byts)
    c = condition(byts)
    if c == "al": c = ""
    
    if op2 == 0:
        inst_dict["group"] = "load"
        if bit_9(byts) == 1:
            if bit_21(byts) == 1:
                """ Move to Register from Banked or Special register B9.3.9
                    MRS<c> <Rd>, <banked_reg>
                """
                return mrs_inst(byts, inst_dict)
            
            else:
                """ Move to Banked or Special register from ARM core register B9.3.10
                    MSR{<c>}{<q>} <banked_reg>, <Rn>
                """ 
                return msr_inst(byts, inst_dict)
            
        else:
            op = bits_21_22(byts)
            if op == 0 or op == 2:
                """ Move to Register from Special register A8.8.109, B9.3.8
                    MRS<c> <Rd>, <spec_reg>
                """
                return msr_inst(byts, inst_dict)
            
            elif op == 1:
                if bits_16_17(byts) == 0:
                    """ Move to Special register from ARM core register A8.8.112
                        MSR<c> <spec_reg>, <Rn>
                    """
                    return msr_inst(byts, inst_dict)
                    
                else:
                    """ Move to Special register from ARM core register B9.3.12
                        MSR<c> <spec_reg>, <Rn>
                    """
                    return msr_inst(byts, inst_dict)
                
            elif op == 3:
                """ Move to Special register from ARM core register B9.3.12
                    MSR<c> <spec_reg>, <Rn>
                """
                return msr_inst(byts, inst_dict)
        
    elif op2 == 1:
        if op == 1:
            """ A8.6.25 Branch and Exchange
                BX<c> Rm
            """
            inst_dict["mnem"] = "bx" + c
            inst_dict["group"] = "exec"
            rm = "r%s" % bits_0_3(byts)
            s_op = {'type': 'imm', 'data': rm}
            inst_dict["s_ops"].append(s_op)
            return inst_dict
        
        elif op == 3:
            """ Count Leading Zeros A8.8.33
                CLZ<c> <Rd>, <Rm>
            """
            inst_dict["mnem"] = "clz" + c
            inst_dict["group"] = "arith"

            rd = "r%s" % bits_12_15(byts)
            d_op = {'type': 'imm', 'data': rd}
            inst_dict["d_op"] = d_op

            rm = "r%s" % bits_0_3(byts)
            s_op = {'type': 'imm', 'data': rd}
            inst_dict["s_ops"].append(s_op)

            return inst_dict
            
    elif op2 == 2:
        """ Branch and Exchange Jazelle A8.8.28
            BXJ<c> <Rm>
        """
        inst_dict["mnem"] = "bxj" + c
        inst_dict["group"] = "exec"

        rm = "r%s" % bits_0_3(byts)
        s_op = {'type': 'imm', 'data': rm}
        inst_dict["s_ops"].append(s_op)

        return inst_dict
    
    elif op2 == 3:
        """ Branch with Link and Exchange (register) A8.8.26
            BLX<c> <Rm>
        """
        inst_dict["mnem"] = "blx" + c
        inst_dict["group"] = "exec"

        rm = "r%s" % bits_0_3(byts)
        s_op = {'type': 'imm', 'data': rm}
        inst_dict["s_ops"].append(s_op)
        
        return inst_dict
    
    elif op2 == 5:
        """ Saturating addition and subtraction A5.2.6
        """
        op = bits_21_22(byts)
        inst_dict["group"] = "arith"
        if op == 0:
            """ Saturating Add A8.8.134
                QADD<c> <Rd>, <Rm>, <Rn
            """
            inst_dict["mnem"] = "qadd" + c
            return saturating_add_sub_inst(byts, inst_dict)
            
        elif op == 1:
            """ Saturating Subtract A8.8.141
                QSUB<c> <Rd>, <Rm>, <Rn>
            """
            inst_dict["mnem"] = "qsub" + c
            return saturating_add_sub_inst(byts, inst_dict)
        
        elif op == 2:
            """ Saturating Double and Add
                QDADD<c> <Rd>, <Rm>, <Rn>
            """
            inst_dict["mnem"] = "qdadd" + c
            return saturating_add_sub_inst(byts, inst_dict)
            
        else: #op == 3
            """ Saturating Double and Subtract A8.8.139
                QDSUB<c> <Rd>, <Rm>, <Rn>
            """
            inst_dict["mnem"] = "qdsub" + c
            return saturating_add_sub_inst(byts, inst_dict)
        
    elif op2 == 7:
        inst_dict["group"] = "other"
        inst_dict["mnem"] = "SMC B6-18"
        return inst_dict
    
    inst_dict["group"] = "invalid"
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict    


def msr_inst(byts, inst_dict):
    """ Helper function for msr instructions
        MSR<c> <spec_reg>, <Rn>
    """
    c = condition(byts)
    if c == "al": c = ""
    
    inst_dict["mnem"] = "msr" + c
    inst_dict["group"] = "system"
    
    d_op = {'type': 'imm', 'data': "<APSR>"}
    inst_dict["d_op"] = d_op

    rn = "r" + str(bits_0_3(byts))
    s_op = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op)

    return inst_dict 
   

def mrs_inst(byts, inst_dict):
    """ Helper function for mrs instructions
        MRS<c> <Rd>, <spec_reg>
    """
    c = condition(byts)
    if c == "al": c = ""
    inst_dict["mnem"] = "mrs" + c
    
    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op
    
    s_op = {'type': 'imm', 'data': "<APSR>"}
    inst_dict["s_ops"].append(s_op)

    return inst_dict 


def data_processing_register_shifted(byts, inst_dict):
    """ A5.2.2
    """
    op1 = bits_20_24(byts)
              
    if op1 == 0 or op1 == 1:
        """ A8.6.13 Bitwise AND
            AND{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "and"
        inst_dict["group"] = "logic"
        return dp_reg_shifted_ops(byts, inst_dict)
        
    elif op1 == 2 or op1 == 3:
        """ A8.6.46 Bitwise Exclusive OR
            EOR{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "eor"
        inst_dict["group"] = "logic"
        return dp_reg_shifted_ops(byts, inst_dict)
        
    elif op1 == 4 or op1 == 5:
        """ A8.6.214 Subtract
            SUB{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "sub"
        inst_dict["group"] = "arith"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 6 or op1 == 7:
        """ A8.6.144 Reverse Subtract
            RSB{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "rsb"
        inst_dict["group"] = "arith"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 8 or op1 == 9:
        """ A8.6.7 Add
            ADD{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "add"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 10 or op1 == 11:
        """ A8.6.3 Add with Carry
            ADC{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "adc"
        inst_dict["group"] = "arith"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 12 or op1 == 13:
        """ A8.6.153 Subtract with Carry
            SBC{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "sbc"
        inst_dict["group"] = "arith"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 14 or op1 == 15:
        """ A8.6.147 Reverse Subtract with Carry
            RSC{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "rsc"
        inst_dict["group"] = "arith"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 17:
        """ A8.6.232 Test
            TST<c> <Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "tst"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
    
    elif op1 == 19:
        """ A8.6.229 Test Equivalence
            TEQ<c> <Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "teq"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
    
    elif op1 == 21:
        """ A8.6.37 Compare
            CMP<c> <Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "cmp"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
    
    elif op1 == 23:
        """ A8.6.34 Compare Negative
            CMN<c> <Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "cmn"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
    
    elif op1 == 24 or op1 == 25:
        """ A8.6.115 Bitwise OR 
            ORR{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "orr"
        inst_dict["group"] = "logic"
        return dp_reg_shifted_shift_ops(byts, inst_dict)
    
    elif op1 == 26 or op1 == 27:
        op2 == bits_5_6(byts)
        if op2 == 0 :
            """ A8.6.89 Logical Shift Left
                LSL{S}<c> <Rd>,<Rn>,<Rm>
            """
            inst_dict["mnem"] = "lsl"
            inst_dict["group"] = "logic"
            return dp_reg_shifted_shift_ops(byts, inst_dict)
        
        elif op2 == 1 :
            """ A8.6.91 Logical Shift Right
                LSR{S}<c> <Rd>,<Rn>,<Rm>
            """
            inst_dict["mnem"] = "lsr" 
            inst_dict["group"] = "logic"
            return dp_reg_shifted_shift_ops(byts, inst_dict)       
        
        elif op2 == 2 :
            """ A8.6.15 Arithmetic Shift Right
                ASR{S}<c> <Rd>,<Rn>,<Rm>
            """
            inst_dict["mnem"] = "asr"
            inst_dict["group"] = "logic"
            return dp_reg_shifted_shift_ops(byts, inst_dict)
                    
        elif op2 == 3 :
            """ A8.6.140 Rotate Right
                ROR{S}<c> <Rd>,<Rn>,<Rm>
            """
            inst_dict["mnem"] = "ror"
            inst_dict["group"] = "logic"
            return dp_reg_shifted_shift_ops(byts, inst_dict)
    
    elif op1 == 28 or op1 == 29:
        """ A8.6.21 Bitwise Bit Clear
            BIC{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "bic"
        inst_dict["group"] = "flag"
        return dp_reg_shifted_ops(byts, inst_dict)
    
    elif op1 == 30 or op1 == 31:
        """ A8.6.108 Bitwise NOT
            MVN{S}<c> <Rd>,<Rm>,<type> <Rs>
        """
        inst_dict["mnem"] = "mvn" 
        inst_dict["group"] = "flag"
        return dp_reg_shifted_ops(byts, inst_dict)           

    inst_dict["group"] = "invalid"
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict


def dp_reg_shifted_ops(byts, inst_dict):
    """ Helper function for data processing register instructions with 3 operands
        MNEM{S}<c> <Rd>,<Rn>,<Rm>,<type> <Rs>
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al":
        inst_dict["mnem"] += c        

    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    rn = "r%s"  % +bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s"  % +bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)
    
    shift_type = get_shift_type(bits_5_6(byts))
    rs = "r%s" % shift_type, bits_8_11(byts)
    s_op3 = {'type': 'imm', 'data': rs}
    inst_dict["s_ops"].append(s_op3)

    return inst_dict


def dp_reg_shifted_shift_ops(byts, inst_dict):
    """ Helper function for shift register instructions 
        MNEM{S}<c> <Rd>,<Rn>,<Rm>
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al":
        inst_dict["mnem"] += c

    rd = "r%s" % bits_12_15(byts)    
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    rn = "r%s" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s" % bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)
    
    return inst_dict
    
    
def dp_reg_test_ops(byts, inst_dict):
    """ Helper function for test register instructions 
        MNEM<c> <Rn>,<Rm>,<type> <Rs>
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al":
        inst_dict["mnem"] += c     

    d_op = {'type': 'imm', 'data': "<APSR>"}
    inst_dict["d_op"] = d_op

    rn = "r%s"  % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "r%s"  % +bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)
    
    shift_type = get_shift_type(bits_5_6(byts))
    rs = "r%s" % shift_type, bits_8_11(byts)
    s_op3 = {'type': 'imm', 'data': rs}
    inst_dict["s_ops"].append(s_op3)
    return inst_dict    
    

def data_processing_immediate(byts, inst_dict):
    """ A5.2.3
    """
    op = bits_20_24(byts)
    rn = "r" + str(bits_16_19(byts))
    rd = "r" + str(bits_12_15(byts))
    imm12 = "#" + hex(bits_0_11(byts)) # FIXME ARMExpandImm(imm12)
    c = condition(byts)
    if c == "al": c = ""
        
    if op == 0 or op == 1:
        """ A8.6.11 Bitwise AND
            AND{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "and"
        inst_dict["group"] = "logic"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 2 or op == 3:
        """ A8.6.44 Bitwise Exclusive OR
            EOR{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "eor"
        inst_dict["group"] = "logic"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 4 or op == 5:
        if rn != "r15": 
            """ A8.6.212 Subtract
                SUB{S}<c> <Rd>,<Rn>,#<const>
            """
            inst_dict["mnem"] = "sub"
            inst_dict["group"] = "arith"
            return dp_imm_3_ops(byts, inst_dict)
            
        else: 
            """ A8.6.10 Form PC-relative address
                ADR<c> <Rd>,<label>
            """
            inst_dict["mnem"] = "adr"
            inst_dict["group"] = "arith"
            return dp_imm_2_ops(byts, inst_dict)
            
    elif op == 6 or op == 7:
        """ A8.6.142 Reverse Subtract
            RSB{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "rsb"
        inst_dict["group"] = "arith"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 8 or op == 9:
        if rn != "r15":
            """ A8.6.5 Add
                ADD{S}<c> <Rd>,<Rn>,#<const>
            """
            inst_dict["mnem"] = "add"
            inst_dict["group"] = "arith"
            return dp_imm_3_ops(byts, inst_dict)
            
        else:
            """ A8.6.10 Form PC-relative address
                ADR<c> <Rd>,<label>
            """
            inst_dict["mnem"] = "adr"
            inst_dict["group"] = "arith"
            return dp_imm_2_ops(byts, inst_dict)
            
    elif op == 10 or op == 11:
        """ A8.6.1 Add with Carry
            ADC{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "adc"
        inst_dict["group"] = "arith"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 12 or op == 13:
        """ A8.6.151 Subtract with Carry
            SBC{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "sbc"
        inst_dict["group"] = "arith"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 14 or op == 15:
        """ A8.6.145 Reverse Subtract with Carry
            RSC{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "rsc"
        inst_dict["group"] = "arith"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 17:
        """ A8.6.230 Test
            TST<c> <Rn>,#<const>
        """
        inst_dict["mnem"] = "tst"
        inst_dict["group"] = "flag"
        return dp_imm_test_ops(byts, inst_dict)
        
    elif op == 19:
        """ A8.6.227 Test Equivalence
            TEQ<c> <Rn>,#<const>
        """
        inst_dict["mnem"] = "teq"
        inst_dict["group"] = "flag"
        return dp_imm_test_ops(byts, inst_dict)
        
    elif op == 21:
        """ A8.6.35 Compare
            CMP<c> <Rn>,#<const>
        """
        inst_dict["mnem"] = "cmp"
        inst_dict["group"] = "flag"
        return dp_imm_test_ops(byts, inst_dict)
        
    elif op == 23:
        """ A8.6.32 Compare Negative
            CMN<c> <Rn>,#<const>
        """
        inst_dict["mnem"] = "cmn"
        inst_dict["group"] = "flag"
        return dp_imm_test_ops(byts, inst_dict)
    
    elif op == 24 or op == 25:
        """ A8.6.113 Bitwise OR
            ORR{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "orr"
        inst_dict["group"] = "logic"
        return dp_imm_3_ops(byts, inst_dict)
        
    elif op == 26 or op == 27:
        """ A8.6.96 Move
            MOV{S}<c> <Rd>,#<const>
              or
            MOVW<c> <Rd>,#<imm16>
        """
        inst_dict["mnem"] = "mov"
        inst_dict["group"] = "load"
        if bits_20_27(byts) == 28:
            inst_dict["mnem"] += "w"
            
            rd = "r%s" % bits_12_15(byts)
            d_op = {'type': 'imm', 'data': rd}
            inst_dict["d_op"] = d_op
            
            imm16 = "#" + hex( (bits_16_19(byts) << 12) + bits_0_11(byts) )
            s_op = {'type': 'imm', 'data': imm16}
            inst_dict["s_ops"] = s_op
            return inst_dict
        
        else:
            if bit_20(byts) == 1:
                inst_dict["mnem"] += "s"
            return dp_imm_2_ops(byts, inst_dict)
    
    elif op == 28 or op == 29:
        """ A8.6.19 Bitwise Bit Clear
            BIC{S}<c> <Rd>,<Rn>,#<const>
        """
        inst_dict["mnem"] = "bic"
        inst_dict["group"] = "flag"
        return dp_imm_3_ops(byts, inst_dict)
    
    elif op == 30 or op == 31:
        """ A8.6.106 Bitwise NOT
            MVN{S}<c> <Rd>,#<const>
        """
        inst_dict["mnem"] = "mvn"
        inst_dict["group"] = "load"
        return dp_imm_2_ops(byts, inst_dict)
    
    inst_dict["mnem"] = "<UNKNOWN>"
    inst_dict["group"] = "invalid" 
    return inst_dict


def dp_imm_3_ops(byts, inst_dict):
    """ Helper function for data processing immediate operands
        MNEM{S}<c> <Rd>,<Rn>,#<const>
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c

    rd = "r" + str(bits_12_15(byts))
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    rn = "r" + str(bits_16_19(byts))
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    imm12 = "#" + hex(bits_0_11(byts)) 
    s_op2 = {'type': 'imm', 'data': imm12}
    inst_dict["s_ops"].append(s_op2)

    return inst_dict
    
def dp_imm_2_ops(byts, inst_dict):
    """ Helper function for data processing immediate operands
        MNEM<c> <Rd>,<label>
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c

    rd = "r" + str(bits_12_15(byts))
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    imm12 = "#" + hex(bits_0_11(byts)) 
    s_op2 = {'type': 'imm', 'data': imm12}
    inst_dict["s_ops"].append(s_op2)

    return inst_dict

def dp_imm_test_ops(byts, inst_dict):
    """ Helper function for data processing immediate operands
        MNEM<c> <Rn>,#<const>
    """
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c

    rn = "r" + str(bits_16_19(byts))
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    imm12 = "#" + hex(bits_0_11(byts)) 
    s_op2 = {'type': 'imm', 'data': imm12}
    inst_dict["s_ops"].append(s_op2)

    return inst_dict


def data_processing_register(byts, inst_dict):
    """ A5.2.1
    """ 
    op1 = bits_20_24(byts)
    
    if op1 == 16 or op1 == 18 or op1 == 20 or op1 == 22:
        inst_dict["mnem"] = "Data-processing and misc A5-4"
    
    op1_1 = bits_21_24(byts)
    if op1_1 == 0:
        """ A8.6.12 Bitwise AND
            AND{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "and"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 1:
        """ A8.6.45 Bitwise Exclusive OR
            EOR{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "eor"
        inst_dict["group"] = "logic"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 2:
        """ A8.6.213 Subtract
            SUB{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "sub"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 3:
        """ A8.6.143 Reverse Subtract 
            RSB{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "rsb"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 4:
        """ A8.6.6 Add
            ADD{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "add"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 5:
        """ A8.6.2 Add with Carry
            ADC{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "adc"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 6:
        """ A8.6.152 Subtract with Carry
            SBC{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "sbc"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 7:
        """ A8.6.146 Reverse Subtract with Carry
            RSC{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "rsc"
        inst_dict["group"] = "arith"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 8:
        """ A8.6.231 Test
            TST<c> <Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "tst"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
        
    elif op1_1 == 9:
        """ A8.6.228 Test Equivalence
            TEQ<c> <Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "teq"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
        
    elif op1_1 == 10:
        """ A8.6.36 Compare
            CMP<c> <Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "cmp"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
        
    elif op1_1 == 11:
        """ A8.6.33 Compare Negative
            CMN<c> <Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "cmn"
        inst_dict["group"] = "flag"
        return dp_reg_test_ops(byts, inst_dict)
        
    elif op1_1 == 12:
        """ A8.6.114 Bitwise OR
            ORR{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "orr"
        inst_dict["group"] = "logic"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 13:
        op2 = bits_5_6(byts)
        imm5 = "#" + hex(bits_7_11(byts)) 
        if imm5 == "#0x0":
            rm = "r" + str(bits_0_3(byts))
            rd = "r" + str(bits_12_15(byts))
            if op2 == 0:
                """ A8.6.97 Move
                    MOV{S}<c> <Rd>,<Rm>
                """
                inst_dict["group"] = "load"
                inst_dict["mnem"] = "mov"
                if bit_20(byts) == 1:
                    inst_dict["mnem"] += "s"

                d_op = {'type': 'imm', 'data': rd}
                inst_dict["d_op"] = d_op

                s_op = {'type': 'imm', 'data': rm}
                inst_dict["s_ops"].append(s_op)

                return inst_dict

                        
            elif op2 == 3:
                """A8.6.141  Rotate Right with Extend
                    RRX{S}<c> <Rd>,<Rm>
                """
                inst_dict["group"] = "logic"
                inst_dict["mnem"] = "rrx"
                if bit_20(byts) == 1:
                    inst_dict["mnem"] += "s"
                
                d_op = {'type': 'imm', 'data': rd}
                inst_dict["d_op"] = d_op

                s_op = {'type': 'imm', 'data': rm}
                inst_dict["s_ops"].append(s_op)
                
                return inst_dict

        else: # op2 != "#0x0"
            if op2 == 0:
                """ A8.6.88 Logical Shift Left
                    LSL{S}<c> <Rd>,<Rm>,#<imm5>
                """
                inst_dict["mnem"] = "lsl"
                inst_dict["group"] = "logic"
                return dp_reg_shift_ops(byts, inst_dict)
            
        
            elif op2 == 1:
                """ Logical Shift Right
                    LSR{S}<c> <Rd>,<Rm>,#<imm>
                """
                inst_dict["mnem"] = "lsr"
                inst_dict["group"] = "logic"
                return dp_reg_shift_ops(byts, inst_dict)
            
            elif op2 == 2:
                """ A8.6.14 Arithmetic Shift Right
                    ASR{S}<c> <Rd>,<Rm>,#<imm>
                """
                inst_dict["mnem"] = "asr"
                inst_dict["group"] = "logic"
                return dp_reg_shift_ops(byts, inst_dict)
            
            elif op2 == 3:
                """ A8.6.139 Rotate Right
                    ROR{S}<c> <Rd>,<Rm>,#<imm>
                """
                inst_dict["mnem"] = "ror"
                inst_dict["group"] = "logic"
                return dp_reg_shift_ops(byts, inst_dict)

    elif op1_1 == 14:
        """ A8.6.20 Bitwise Bit Clear
            BIC{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "bic"
        inst_dict["group"] = "flag"
        return dp_reg_ops(byts, inst_dict)
        
    elif op1_1 == 15:
        """ A8.6.107 Bitwise NOT
            MVN{S}<c> <Rd>,<Rm>{,<shift>}
        """
        inst_dict["mnem"] = "mvn"
        inst_dict["group"] = "logic"
        if bit_20(byts) == 1:
            inst_dict["mnem"] += "s"
        c = condition(byts)
        if c != "al": 
            inst_dict["mnem"] += c

        rd = "r%s" % bits_12_15(byts)
        d_op = {'type': 'imm', 'data': rd}
        inst_dict["d_op"] = d_op

        rm = "r%s" % bits_0_3(byts)
        s_op2 = {'type': 'imm', 'data': rm}
        inst_dict["s_ops"].append(s_op2)

        imm5 = "#" + hex(bits_7_11(byts))
        if imm5 != "#0x0":   
            shift_type = get_shift_type(bits_5_6(byts))
            shift = shift_type + imm5
            s_op3 = {'type': 'imm', 'data': shift}
            inst_dict["s_ops"].append(s_op3)

    return inst_dict 

    
    inst_dict["group"] = "invalid"
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict


def dp_reg_ops(byts, inst_dict):
    """ Helper function for data processing register instructions
        MNEM{S}<c> <Rd>,<Rn>,<Rm>{,<shift>}
    """
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c

    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    rn = "r%s" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(rn)

    rm = "r%s" % bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    imm5 = "#" + hex(bits_7_11(byts))
    if imm5 != "#0x0":   
        shift_type = get_shift_type(bits_5_6(byts))
        shift = shift_type + imm5
        s_op3 = {'type': 'imm', 'data': shift}
        inst_dict["s_ops"].append(s_op3)

    return inst_dict 

def dp_reg_shift_ops(byts, inst_dict):
    """ Helper function for data processing register instructions
        MNEM{S}<c> <Rd>,<Rm>,#<imm>
    """  
    if bit_20(byts) == 1:
        inst_dict["mnem"] += "s"
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c

    rd = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': rd}
    inst_dict["d_op"] = d_op

    rm = "r%s" % bits_0_3(byts)
    s_op1 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op1)

    imm5 = "#" + hex(bits_7_11(byts))
    s_op2 = {'type': 'imm', 'data': imm5}
    inst_dict["s_ops"].append(s_op2)
    
    return inst_dict
    
#def dp_reg_test_ops(byts, inst_dict):
#    """ Helper function for data processing register instructions
#        MNEM<c> <Rn>,<Rm>{,<shift>}
#    """  
"""
    c = condition(byts)
    if c != "al": 
        inst_dict["mnem"] += c
    
    rn = "r%s" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(rn)

    rm = "r%s" % bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    imm5 = "#" + hex(bits_7_11(byts))
    if imm5 != "#0x0":   
        shift_type = get_shift_type(bits_5_6(byts))
        shift = shift_type + imm5
        s_op3 = {'type': 'imm', 'data': shift}
        inst_dict["s_ops"].append(s_op3)

    return inst_dict
"""                   
        
def msr_immediate_misc(byts, inst_dict):
    """ A5.2.11
    """
    if bit_22(byts) == 0:
        op1 = bits_16_19(byts)
        c = condition(byts)
        if c == "al": c = "" 
        
        if op1 == 0:
            inst_dict["group"] = "other"
            op2 = bits_0_7(byts)
            if op1 == 0:
                """ No Operation A8.8.119
                    NOP<c>
                """
                inst_dict["mnem"] = "nop" + c
                return inst_dict
                
            elif op1 == 1:
                """ YIELD A8.8.426
                    YIELD<c>
                """ 
                inst_dict["mnem"] = "yield" + c
                return inst_dict
                
            elif op1 == 2:
                """ Wait For Event A8.8.424
                    WFE<c>
                """
                inst_dict["mnem"] = "wfe" + c
                return inst_dict
                
            elif op1 == 3:
                """ Wait For Interrupt A8.8.425
                    WFI<c>
                """
                inst_dict["mnem"] = "wfi" + c
                return inst_dict
                
            elif op1 == 4:
                """ Send Event A8.8.168
                    SEV<c>
                """
                inst_dict["mnem"] = "sev" + c
                return inst_dict
                
            elif op1 >= 240:
                """ Debug A8.8.42
                    DBG<c> #<option>
                """
                option = "#" + str(bits_0_3(byts))
                inst_dict["mnem"] = "debug " + c + " #" + options
                return inst_dict
        
        else: # op1 != 0
            inst_dict["group"] = "load"
            if bits_16_17(byts) == 0:
                """ Move immediate value to Special register A8.8.111
                    MSR<c> <spec_reg>, #<const>
                """
                return msr_immediate_operands(byts, inst_dict)
                
            else:
                """ Move immediate value to Special register B9.3.11
                    MSR<c> <spec_reg>, #<const>
                """
                return msr_immediate_operands(byts, inst_dict)
            
    else: # bit_22(byts) == 1:
        """ Move immediate value to Special register B9.3.11
            MSR<c> <spec_reg>, #<const>
        """
        inst_dict["group"] = "load"
        return msr_immediate_operands(byts, inst_dict)
    
    inst_dict["group"] = "invalid"
    inst_dict["mnem"] = "<UNKNOWN>"
    return inst_dict

def msr_immediate_operands(byts, inst_dict):
    """ msr immediate instruction helper function
        MNEM<c> <spec_reg>, #<const>
    """

    inst_dict["mnem"] = "msr"    
    if c != "al": 
        inst_dict["mnem"] += c

    d_op = {'type': 'imm', 'data': "<SPSR>"}
    inst_dict["s_op"] = d_op
    
    imm12 = "#" + hex(bits_0_11(byts))
    s_op = {'type': 'imm', 'data': imm12}
    inst_dict["s_ops"].append(s_op)

    return inst_dict   


######### LOAD/STORE WORD AND UNSIGNED BYTE ##############################################
def load_store_inst(byts, inst_dict):
    """ A5.3
    """
    op1_1 = (bit_24(byts) << 4) + bits_20_22(byts) # 0b?x???
    op1_2 = (bit_22(byts) << 2) + bit_20(byts) # 0bxx?x?
    a = bit_25(byts)
    c = condition(byts)
    if c == "al": c = "" 
    inst_dict["group"] = "load"
        
    if op1_1 == 2: # 0b0x010
        """ A8.8.220 Store Register Unprivileged
        """
        inst_dict["mnem"] = "strt" + c
        return load_store_memory_access_register(byts, inst_dict)


    elif op1_1 == 3: # 0b0x011
        """ A8.8.92 Load Register Unprivileged
        """
        inst_dict["mnem"] = "ldrt" + c
        return load_store_memory_access_register(byts, inst_dict)


    elif op1_1 == 6: # 0b0x110
        """ A8.8.209 Store Register Byte Unprivileged
        """
        inst_dict["mnem"] = "strbt" + c
        return load_store_memory_access_register(byts, inst_dict)
    
        
    elif op1_1 == 7: # 0b0x111
        """ A8.8.71 Load Register Byte Unprivileged
        """
        inst_dict["mnem"] = "ldrbt" + c
        return load_store_memory_access_register(byts, inst_dict)
    
    
    elif op1_2 == 0: # 0bxx0x0 not 0b0x010
        if a == 0:
            """ A8.8.205 Store Register (register)
            """
            inst_dict["mnem"] = "str" + c
            return load_store_memory_access_register(byts, inst_dict)
            
        else: # a != 0
            inst_dict["mnem"] = "STRT on page A8-706 A8.8.220"
            return load_store_memory_access_register(byts, inst_dict)
    
    
    elif op1_2 == 0: # xx0x0 not 0x010
        if a == 0:
            """ A8.8.204 Store Register (immediate)        
            """
            inst_dict["mnem"] = "str" + c
            return load_store_memory_access_immediate(byts, inst_dict)
            
        else: # a != 0
            """ A8.8.205 Store Register (register)
            """
            inst_dict["mnem"] = "str" + c
            return load_store_memory_access_register(byts, inst_dict)
            
            
    elif op1_2 == 1: # 0bxx0x1 not 0x011
        if a == 0:
            if bits_16_19(byts) != 15: # rn
                """ A8.8.63 Load Register (immediate)
                """
                inst_dict["mnem"] = "ldr" + c
                return load_store_memory_access_immediate(byts, inst_dict)
            
            else: # rn == 15
                """ A8.8.64 Load Register (literal)
                """
                inst_dict["mnem"] = "ldr" + c
                return load_store_memory_access_literal(byts, inst_dict)
                
        else: # a!=0
            """ A8.8.66 Load Register (register)
            """
            inst_dict["mnem"] = "ldr" + c
            return load_store_memory_access_register(byts, inst_dict)
            
  
    elif op1_2 == 2: # xx1x0 not 0x110
        if a == 0:
            """ A8.8.207 Store Register Byte (immediate)
            """
            inst_dict["mnem"] = "strb" + c
            return load_store_memory_access_immediate(byts, inst_dict)

        else: # a != 0
            """ A8.8.208 Store Register Byte (register)
            """ 
            inst_dict["mnem"] = "strb" + c
            return load_store_memory_access_register(byts, inst_dict)  
            
            
    elif op1_2 == 1: # xx1x1 not not 0x111
        if a == 0:
            if bits_16_19(byts) != 15: # rn
                """ A8.8.68 Load Register Byte (immediate) 
                """
                inst_dict["mnem"] = "ldrb" + c
                return load_store_memory_access_immediate(byts, inst_dict)
                
            else: # r != 15
                """ A8.8.69 Load Register Byte (literal)
                """
                inst_dict["mnem"] = "ldrb" + c
                return load_store_memory_access_literal(byts, inst_dict)
    
        else: # a != 0 
            """ A8.8.70 Load Register Byte (register)
            """
            inst_dict["mnem"] = "ldrb" + c
            return load_store_memory_access_register(byts, inst_dict)
            

    inst_dict["mnem"] = "<UNKNOWN>"
    inst_dict["group"] = "invalid"
    return inst_dict


def load_store_memory_access_literal(byts, inst_dict):
    """ Helper function for load store instuctions A5.3
        MNEM{<c>}{<q>} <rt>, <label>
        MNEM{<c>}{<q>} <rt>, [PC, #+/-<imm>]]
    """
    rt = "r" + str(bits_12_15(byts)) 
    imm12 = "#" + hex(bits_0_11(byts))  
    inst_dict["d_ops"].append(rt)
    inst_dict["s_ops"].append(imm12) 


def load_store_memory_access_register(byts, inst_dict):
    """ Helper function for load store instructions A5.3
        MNEM{<c>}{<q>} <Rt>, [<Rn>, <Rm>{, <shift>}]  # index==True,  wback==False
        MNEM{<c>}{<q>} <Rt>, [<Rn>, <Rm>{, <shift>}]! # index==True,  wback==True
        MNEM{<c>}{<q>} <Rt>, [<Rn>], <Rm>{, <shift>} # index==False,  wback==True
    """

    rt = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': imm24}
    inst_dict["d_op"] = d_op

    rn = "[r%s]" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    rm = "[r%s]" % bits_0_3(byts)
    s_op2 = {'type': 'imm', 'data': rm}
    inst_dict["s_ops"].append(s_op2)

    imm5 = "[#%s]" % hex(bits_7_11(byts))
    if imm5 != "#0x0":
        s_op3 = {'type': 'imm', 'data': imm5}
        inst_dict["s_ops"].append(s_op3)

    return inst_dict


def load_store_memory_access_immediate(byts, inst_dict):
    """ Helper function for load store instructions A5.3
        MNEM<c> <Rt>, [<Rn>{, #+/-<imm12>}]  # index==True,  wback==False
        MNEM<c> <Rt>, [<Rn>], #+/-<imm12>   # index==True,  wback==True 
        MNEM<c> <Rt>, [<Rn>, #+/-<imm12>]!  # index==False, wback=True
    """
    rt = "r%s" % bits_12_15(byts)
    d_op = {'type': 'imm', 'data': imm24}
    inst_dict["d_op"] = d_op

    rn = "[r%s]" % bits_16_19(byts)
    s_op1 = {'type': 'imm', 'data': rn}
    inst_dict["s_ops"].append(s_op1)

    imm12 = "#%s" %  hex(bits_0_11(byts))
    if imm12 != "#0x0":
        s_op2 = {'type': 'imm', 'data': imm12}
        inst_dict["s_ops"].append(s_op2)

    return inst_dict

# HERE    
######### UNCONDITIONAL INSTRUCTIONS ####################################################
def unconditional_inst(byts, inst_dict):
    """ A5.7
    """
    if bit_27 == 0:
        return unconditional_misc(byts, inst_dict)
    
    op1_1 = bits_25_27(byts)
    if op1_1 == 4:
        if bit_22(byts) == 1 and bit_20(byts) == 0:
            """ Store Return State B9.3.16
                SRS{<amode>} SP{!}, #<mode>
            """
            get_amode(bits_23_24(byts))
            inst_dict["mnem"] = "srs{" + amode + "}"
            inst_dict["group"] = "exec"
            if bit_21(byts) == 1:
                inst_dict["s_ops"].append("r13{!}") # SP
            else:
                inst_dict["s_ops"].append("r13") # SP
                
            mode = "#" + get_processor_mode(bits_0_4(byts))
            inst_dict["s_ops"].append(mode)
            return inst_dict
            
        elif bit_22(byts) == 0 and bit_20(byts) == 1:
            """ Return From Exception B9.3.13
                RFE{<amode>} <Rn>{!}
            """
            get_amode(bits_23_24(byts))
            inst_dict["mnem"] = "rfe{" + amode + "}"
            inst_dict["group"] = "exec"
            rn = "r" + str(bits_16_19(byts))
            if bit_21(byts) == 1:
                inst_dict["s_ops"].append(rn+"{!}")
            else:
                inst_dict["s_ops"].append(rn)
            return inst_dict
            
    elif op1_1 == 5:
        """ Branch with Link (immediate) A8.8.25
            BL<c> <label> # will never get here because this is already unconditional instructions
            BLX <label>
        """
        inst_dict["mnem"] = "blx"
        inst_dict["group"] = "exec"
        inst_dict["addr"] = hex(bits_0_23(byts))
        return inst_dict
    
    elif op1_1 == 6:
        rn == bits_16_19(byts)
        if bit_20(byts) == 0 and bits_23_24(byts) != 0 and bit_21 != 0:
            """ Store Coprocessor A8.8.198
            """
            inst_dict["mnem"] = "stc" 
            inst_dict["group"] = "system"
        
        elif bits_23_24(byts) != 0 and bit_21 != 1:
            if rn != 15:
                inst_dict["mnem"] = "ldc"
                inst_dict["group"] = "system"
                return inst_dict
                
            else:
                inst_dict["mnem"] = "ldc"
                inst_dict["group"] = "system" 
                return inst_dict
    
    op1 = bits_20_27(byts)
    if op1 == 196:
        inst_dict["mnem"] = "mcrr"
        inst_dict["group"] = "system"
        return inst_dict
        
    elif op1 == 197:
        inst_dict["mnem"] = "mrrc"
        inst_dict["group"] = "system"
        return inst_dict
        
    op1_2 = bits_24_27(byts)
    if op1_2 == 14:
        if bit_4(byts) == 1:
            inst_dict["mnem"] = "cdp"
            inst_dict["group"] = "system"
            return inst_dict
            
        elif bit_20(byts) == 0:
            inst_dict["mnem"] = "mcr"
            inst_dict["group"] = "system"
            return inst_dict
            
        else:
            inst_dict["mnem"] = "mrc"
            inst_dict["group"] = "system"
            return inst_dict

            
    inst_dict["mnem"] = "<UNKNOWN>"
    inst_dict["group"] = "invalid"
    return inst_dict

 
def unconditional_misc(byts, inst_dict):
    """ A5.7.1 Memory hints, Advanced SIMD instructions, and miscellaneous instructions
    """
    op1 = bits_20_26(byts)
    op2 = bits_4_7(byts)
    if op1 == 16: # op1==0b0010000
        if bit_5(byts) == 0 and bit_16(byts) == 0: # op2==0bxx0x and rn==0bxxx0
            """ Change Processor State B9.3.2
                CPS<effect> <iflags>{, #<mode>}
                CPS #<mode>
            """
            mode = "#" + hex(bits_0_3(byts))
            effect  = ""
            if bit_8(byts) == 1:
                effect += "a"
            if bit_7(byts) == 1:
                effect += "i"
            if bit_6(byts) == 1:
                effect += "f"                
                
            inst_dict["mnem"] = "cps" + effect
            if mode != "#0x0":
                inst_dict["s_ops"].append(mode)
            return inst_dict
            
        elif op2 == 0 and bit_16(byts) == 1: # op2==0b0000 and rn==0bxxx1
            """ Set Endianness A8.8.167
                SETEND <endian_specifier>
            """
            inst_dict["mnem"] = "setend"
            if bit_9(byts) == 1:
                inst_dict["s_ops"].append("BE")
            else:
                inst_dict["s_ops"].append("LE")
            return inst_dict
    
    if bits_25_26(byts) == 2: # op1==0b01xxxxx
        inst_dict["mnem"] = "vector arith" # FIXME
        inst_dict["mnem"] = "fpu"
        return inst_dict
        
    op1_1 = bits_24_26(byts)
    op1_2 = bits_20_22(byts)
    if op1_1 == 4:
        if bit_20 == 0: # op1==0b100xxx0
            inst_dict["mnem"] = "vector arith" # FIXME
            inst_dict["mnem"] = "fpu"
            return inst_dict
            
        elif bits_20_22(byts) == 5: # op1==0b100x001
            """ Unallocated memory hint (treat as NOP)
            """
            inst_dict["mnem"] = "nop"
            inst_dict["mnem"] = "other"
            return inst_dict
            
        elif bits_20_22(byts) == 5: # op1==0b100x101
            """ Preload Instruction (immediate, literal) A8.8.129
                PLI [<Rn>, #+/-<imm12>] 
                PLI <label> 
                PLI [PC, #-0]
            """
            inst_dict["mnem"] = "pli"
            inst_dict["mnem"] = "system"
            rn = "r" + str(bits_16_19(byts))
            imm12 = "#" + hex(bits_0_11(byts))
            inst_dict["s_ops"].append(rn)
            inst_dict["s_ops"].append(imm12)
            return inst_dict
            
    if op_1 == 5:
        if op1_2 == 1 or (op1_2 == 5 and bits_16_19(byts) != 15): # 0b101x001 or 0b101x101
            """ Preload Data (immediate) A8.8.126
                PLD{W} [<Rn>, #+/-<imm12>]
            """
            inst_dict["mnem"] = "pld"
            inst_dict["mnem"] = "system"
            if bit_22(byts) == 0:
                inst_dict["mnem"] += "w"
            imm12 = "#" + hex(bits_0_11(byts))
            inst_dict["s_ops"].append(rn)
            inst_dict["s_ops"].append(imm12)
            return inst_dict
    
        elif op1_2 == 5 and bits_16_19(byts) != 15:  
            """ Preload Data (literal) A8.8.127
                PLD <label> 
                PLD [PC, #-0]
            """         
            inst_dict["mnem"] = "pld"
            inst_dict["mnem"] = "system"
            imm12 = "#" + hex(bits_0_11(byts))
            inst_dict["s_ops"].append(imm12)
            return inst_dict   
            
    if op == 87: # 0b1010111
        if op2 == 1:
            """ Clear-Exclusive A8.8.32
                CLREX<c>
            """
            inst_dict["mnem"] = "clrex"
            inst_dict["mnem"] = "system"
            return inst_dict
            
        elif op2 == 4:
            """ Data Synchronization Barrier A8.8.44
                DSB{<c>}{<q>} {<option>}
            """
            inst_dict["mnem"] = "dsb"
            return data_barrier_modes(byts, inst_dict)

        elif op2 == 5:
            """ Data Memory Barrier A8.8.43
                DMB <option>
            """
            inst_dict["mnem"] = "dmb"
            inst_dict["mnem"] = "system"
            return data_barrier_modes(byts, inst_dict)
            
        elif op2 == 6:
            """ Instruction Synchronization Barrier A8.8.53
                ISB{<c>}{<q>} {<option>}
            """
            inst_dict["mnem"] = "isb"
            inst_dict["mnem"] = "system"
            return data_barrier_modes(byts, inst_dict)

    if op1_1 == 6 and op1_2 == 1 and bit_4(byts) == 0: # op1==0b110x001 and op2==0bxxx0
        """ Unallocated memory hint (treat as NOP)
        """
        inst_dict["mnem"] = "nop"
        inst_dict["mnem"] = "other"
        return inst_dict         
        
    if op1_1 == 6 and op1_2 == 5 and bit_4(byts) == 0: # op1==0b110x101 and op2==0bxxx0
        """ Preload Instruction (register) A8.8.130
            PLI [<Rn>,+/-<Rm>{, <shift>}]
        """
        inst_dict["mnem"] = "pli"
        inst_dict["mnem"] = "system"
        rm = "r" + str(bits_0_3(byts))
        rn = "r" + str(bits_16_19(byts))
        inst_dict["s_ops"].append("["+rn+"]")
        imm5 = bits_7_11(byts)
        if rm != "r0":
            inst_dict["s_ops"].append("["+rn+"]")
        if imm5 != 0:
            shift_type = get_shift_type(bits_5_6(byts))
            shift = "#" + shift_type + hex(imm5)
            inst_dict["s_ops"].append("{"+shift+"}")
        return inst_dict   
            
    if op1_1 == 7 and bit_4(byts) == 0 and (op1_2 == 1 or op1_2 == 5): 
        # (op1==111x001 or op1==111x101) and op2==0bxxx0
        """ Preload Data (register) A8.8.128
            PLD{W} [<Rn>,+/-<Rm>{, <shift>}]
        """
        inst_dict["mnem"] = "pld"
        inst_dict["mnem"] = "system"
        if bit_22(byts) == 0:
            inst_dict["mnem"] += "w"
        rm = "r" + str(bits_0_3(byts))
        rn = "r" + str(bits_16_19(byts))
        inst_dict["s_ops"].append("["+rn+"]")
        imm5 = bits_7_11(byts)
        if rm != "r0":
            inst_dict["s_ops"].append("["+rn+"]")
        if imm5 != 0:
            shift_type = get_shift_type(bits_5_6(byts))
            shift = "#" + shift_type + hex(imm5)
            inst_dict["s_ops"].append("{"+shift+"}")
        return inst_dict    
        
            
    inst_dict["mnem"] = "unconditional_misc: <UNKNOWN>"
    return inst_dict 
    
    
def data_barrier_modes(byts, inst_dict):
    """ Helper function for data barrier modes
    """
    option = bits_0_3(byts)
    if option == 15:
        inst_dict["s_ops"].append("{SY}")
    elif option == 14:
        inst_dict["s_ops"].append("{ST}")
    elif option == 11:
        inst_dict["s_ops"].append("{ISH}")
    elif option == 10:
        inst_dict["s_ops"].append("{ISHST}")    
    elif option == 7:
        inst_dict["s_ops"].append("{NSH}")
    elif option == 6:
        inst_dict["s_ops"].append("{NSHST}")
    elif option == 3:
        inst_dict["s_ops"].append("{OSH}")
    elif option == 2:
        inst_dict["s_ops"].append("{OSHST}")
    return inst_dict
    
    
######### SUPERVISOR CALL AND COPROCESSOR ################################################
def supervisor_inst(byts, inst_dict):
    """ Coprocessor instructions, and Supervisor Call A5.6
    """
    inst_dict["mnem"] = "cdp" # FIXME
    inst_dict["mnem"] = "system"
    return inst_dict
    
        
######### UTILITY FUNCTIONS ##############################################################    
def get_amode(amode):
    """ Assume that amode is a two bit value corresponding to bit P, U
    """
    if amode == 0:
        return "da"
    elif amode == 1:
        return "ia"
    elif amod == 2:
        return "db"
    else:
        return "ib"
        

def get_processor_mode(mode):
    """ Assume mode is 5 bits, B1.3.1
    """
    if mode == 16:
        return "usr"
    elif mode == 17:
        return "fiq"
    elif mode == 18:
        return "irq"
    elif mode == 19:
        return "svc"
    elif mode == 22:
        return "mon"
    elif mode == 23:
        return "abt"
    elif mode == 26:
        return "hyp"
    elif mode == 27:
        return "und"
    elif mode == 31:
        return "sys"
    else:
        return "<UNDEFINED>" 
    
    
def get_reg_list(byts):
    """ Given a 4 bytes, assume that the register list is comprised of the first two bytes
        and that each bit corresponds to a register (e.g. byte 1 denotes register 1). 
        Return a list of denoted registers.
    """
    reg_list = []
    for i in range(8):
        if ((ord(byts[0])) >> i) & 0b1:
            reg_list.append("r%s"%i) 

    for i in range(8):
        if ((ord(byts[1])) >> i) & 0b1:
            reg_list.append("r%s"%(i+8))

    return reg_list
         
              
def get_shift_type(tbits):
    """ Assuming a 2 bit value (e.g. range 0 to 3)
    """
    if tbits == 0:
        return "lsl"
    elif tbits == 1:
        return "lsr"
    elif tbits == 2:
        return "asr"
    else:
        return "ror"

        
# IMEDIATE VALUES
def imm16(byts):
    """ imm16 = imm4:imm12
    """
    imm4 = bits_16_19(byts)
    imm12 = bits_0_11(byts)
    imm16 = "#" + hex( (imm4 << 12) + imm12 )
    return imm16


def imm12(byts):
    imm12 = "#" + hex( bits_0_11(byts) )
    return imm12
        
######### MAIN FOR TESTING ###############################################################
if __name__ == "__main__":
    instrs0 = [
        ("\x04\x20\x8F\xE2", "adr r2, 0x80D4"),
        ("\x04\x30\x8F\xE2", "adr r3, 0x80D8"),
        ("\x01\x30\x84\xE3", "orr r3, r4, #1"),
        ("\x03\x00\x12\xE3", "tst r2, #3"),
        ("\x00\x00\x51\xE3", "cmp r1, #0"),
        ("\x02\xC0\x0C\xE0", "and r12, r12, r2"),
        ("\x02\x4A\x04\xE2", "and r4, r4, #0x2000"),
        ("\x03\xC0\xC3\xE3", "bic r12, r3, #0x3"),
        
    ]
    
    instrs1 = [
        ("\xA2\xC3\x41\xE0", "sub r12, r1, r2,LSR#7"),
        ("\x1F\x30\x40\xE2", "sub r3, r0, #FFFF0FFF"),
        ("\x1F\xC0\x4E\xE2", "sub r12, r14(lr), #0x1F"),
        ("\x00\x40\x52\xE2", "subs r4, r2, #0"),
        ("\x01\x20\x62\xE0", "rsb r2, rr, r1"),
        ("\x04\xB0\x8D\xE2", "add r11, r13(sp), #4"),
        ("\x03\x30\x8F\xE0", "add r3, r15(pc), r3"),
        ("\x04\x40\x8F\xE0", "add r4, r15(pc), r4"),
        ("\x11\x32\x10\xE0", "adds r3, r0, r1, lsl r2"),
        ("\x16\x00\x80\x02", "addeq r0, r0, #0x16"),
        
    ]
    
    instrs2 = [
        ("\x01\x20\xE0\xE1", "mvn r2, r1"),
        ("\x00\x30\xA0\xE3", "mov r3, #0"),
        ("\x00\x00\xA0\xE3", "mov r0, #0"),
        ("\x00\x10\xA0\xE3", "mov r1, #0"),
        ("\x03\x00\xA0\xE1", "mov r0, r3"),
        ("\x0D\x00\xA0\xE1", "mov r0, r13(sp)"),
        ("\x23\xCA\xB0\xE1", "movs r12, r3, LSR#20"),
        ("\x22\x70\xA0\x83", "movhi r7, #0x22"),
    ]
    
    instrs3 = [
        ("\x7C\x3A\x00\xEA", "b 0x16AC8" ),
        ("\x05\x00\x00\xEA", "b 0x80F0" ),
        ("\x0D\x00\x00\x1A", "bne <addr>"),
        ("\x09\x00\x00\x0A", "beq <addr>"),
        ("\x7D\x3A\x00\xEB", "bl <0x...>" ),
        ("\x1E\xFF\x2F\xE1", "bx r14(lr)"),
        ("\x33\xff\x2F\xE1", "blx r3"),
        ("\x3C\xff\x2F\xE1", "blx r12"),
            
    ]
 
    instrs4 = [
        ("\x00\x40\x90\xE5", "ldr r4, [r0]"),
        ("\x04\x20\x9D\xE5", "ldr r2, [r13(sp),#0x4]"),
        ("\xB4\x91\x01\x00", "streqh r9, [r1], -r4"),
    ]
    
    instrs5 = [
        ("\x00\x48\x2D\xE9", "stmfd r13(sp)!, {r11, r14(lr)}"),
        ("\x00\x48\x2D\xE9", "stmfd r13(sp)!, {r11,r14(lr)}"),        
        ("\x0F\x00\x84\xE8", "stmia r4, {r0-r3}"),
        ("\x08\x10\x8D\xE8", "stmea r13(sp), {r3, r12}"),
        ("\x03\x00\x94\xE8", "ldmia r4, {r0,r1}"),
        ("\x10\x00\xBD\xE8", "ldmfd r13(sp)!, {r4}"), 
        ("\x04\x10\x90\xE9", "ldmib r0, {r2,r12}"),       
    ]
    
    instrs6 = [
        ("\x02\xF0\x2C\xEE", "cdp p0, 2, c15,c12,c2, 0"),
        ("\x93\xD2\x84\xE0", "umull r14(lr), r4, r3, r2"),
        ("\x00\x00\xA0\xE1", "nop"),
    ]
    
    instrs = []
    instrs.extend(instrs0)
    instrs.extend(instrs1)
    instrs.extend(instrs2)
    instrs.extend(instrs3)
    instrs.extend(instrs4)
    instrs.extend(instrs5)
    instrs.extend(instrs6)
    
    for i in instrs:
        print "-"*95
        try:
            x = decode(i[0])
            m = x["mnem"]
            s = ",".join( [s["data"] for s in x["s_ops"]] )
            if x["d_op"] == {}:
                d = "<NONE>"
            else:
                d = x["d_op"]["data"]
            a = x["addr"]
            c = x["cond"]
        except KeyError as e:
            print "KeyError: %s" % (e)
            print x 
            exit()

        except TypeError as e:
            print "TypeError: %s" % (e)
            print x 
            exit()

        print " %s --> mnem:%s  dst:%s  src:%s addr:%s cond:%s" % (i[1], m, d, s, a, c)
    print "-"*95
        

###################### UNCLASSIFIED // OFFICIAL USE ONLY #################################
