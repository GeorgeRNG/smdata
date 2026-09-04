local b64chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/'

function decodeBase64(input)
    local b64lookup = {}

    for i = 1, #b64chars do
        b64lookup[string.sub(b64chars, i, i)] = i - 1
    end

    b64lookup['='] = 0

    local output = {}
    local buffer = 0
    local bitsCollected = 0

    for i = 1, #input do
        local char = string.sub(input, i, i)
        local value = b64lookup[char]
        
        if value == nil then
            error("Invalid Base64 character: " .. char)
        end

        buffer = bit.bor(bit.lshift(buffer, 6), value)
        bitsCollected = bitsCollected + 6

        if bitsCollected >= 8 then
            bitsCollected = bitsCollected - 8
            local byte = bit.band(bit.rshift(buffer, bitsCollected), 0xFF)

            table.insert(output, string.char(byte))
        end
    end

    return table.concat(output)
end

function encodeBase64(input)
    local output = {}
    local len = #input
    local i = 1

    while i <= len do
        local a, b, c = input:byte(i, i+2)
        local bits = bit.bor(bit.lshift(a or 0, 16), bit.lshift(b or 0, 8), (c or 0))

        table.insert(output, string.sub(b64chars, bit.band(bit.rshift(bits, 18), 0x3F) + 1, bit.band(bit.rshift(bits, 18), 0x3F) + 1))
        table.insert(output, string.sub(b64chars, bit.band(bit.rshift(bits, 12), 0x3F) + 1, bit.band(bit.rshift(bits, 12), 0x3F) + 1))

        if b then
            table.insert(output, string.sub(b64chars, bit.band(bit.rshift(bits, 6), 0x3F) + 1, bit.band(bit.rshift(bits, 6), 0x3F) + 1))
        end

        if c then
            table.insert(output, string.sub(b64chars, bit.band(bits, 0x3F) + 1, bit.band(bits, 0x3F) + 1))
        end

        i = i + 3
    end

    return table.concat(output)
end

function decodeLZ4(input)
    local inputLength = #input
    local inputPos = 1
    local output = {}

    local function readByte()
        local byte = input:byte(inputPos)
        inputPos = inputPos + 1

        return byte
    end

    local function readBytes(count)
        local bytes = string.sub(input, inputPos, inputPos + count - 1)
        inputPos = inputPos + count

        return bytes
    end

    local function readUInt16LE()
        local b1 = readByte()
        local b2 = readByte()

        return b1 + bit.lshift(b2, 8)
    end

    while inputPos <= inputLength do
        local token = readByte()
        local literalLength = bit.rshift(token, 4)
        local matchLength = bit.band(token, 0x0F) + 4

        if literalLength == 15 then
            local len

            repeat
                len = readByte()
                literalLength = literalLength + len
            until len < 255
        end

        if literalLength > 0 then
            local literals = readBytes(literalLength)

            for i = 1, #literals do
                table.insert(output, string.sub(literals, i, i))
            end
        end

        if inputPos > inputLength then
            break
        end

        local offset = readUInt16LE()

        if matchLength == 19 then
            local len

            repeat
                len = readByte()
                matchLength = matchLength + len
            until len < 255
        end

        local outputLength = #output

        for i = 1, matchLength do
            local matchPos = outputLength - offset + i

            table.insert(output, output[matchPos])
        end
    end

    return table.concat(output)
end

function encodeLZ4(input)
    local inputLength = #input

    local inputBytes = {}
    for i = 1, #input do
        inputBytes[i] = input:byte(i)
    end

    local i = 1
    local output = {}
    local literalStart = 1

    while i <= inputLength do
        local bestLength, bestOffset = 0, 0
        local searchStart = (i > 65535) and (i - 65535) or 1

        for j = searchStart, i - 1 do
            local length = 0
            while (i + length <= inputLength) and (inputBytes[j + length] == inputBytes[i + length]) do
                length = length + 1
            end

            if length > bestLength and length >= 4 then
                local compressedSize = 2 + length
                if compressedSize >= 15 then
                    bestLength = length
                    bestOffset = i - j
                    if bestLength == inputLength - i + 1 then break end
                end
            end
        end

        if bestLength >= 4 then
            local literalLength = i - literalStart
            local tokenLiteral = (literalLength < 15) and literalLength or 15
            local tokenMatch = ((bestLength - 4) < 15) and (bestLength - 4) or 15
            output[#output + 1] = string.char(bit.bor(bit.lshift(tokenLiteral, 4), tokenMatch))

            if literalLength >= 15 then
                local len = literalLength - 15
                while len >= 255 do
                    output[#output + 1] = string.char(255)
                    len = len - 255
                end
                output[#output + 1] = string.char(len)
            end

            if literalLength > 0 then
                output[#output + 1] = string.sub(input, literalStart, i - 1)
            end

            output[#output + 1] = string.char(bit.band(bestOffset, 0xFF))
            output[#output + 1] = string.char(bit.rshift(bestOffset, 8))

            if bestLength - 4 >= 15 then
                local len = bestLength - 4 - 15
                while len >= 255 do
                    output[#output + 1] = string.char(255)
                    len = len - 255
                end
                output[#output + 1] = string.char(len)
            end

            i = i + bestLength
            literalStart = i
        else
            i = i + 1
        end
    end

    if literalStart <= inputLength then
        local literalLength = inputLength - literalStart + 1
        if literalLength > 0 then
            local tokenLiteral = (literalLength < 15) and literalLength or 15
            output[#output + 1] = string.char(bit.lshift(tokenLiteral, 4))
    
            if literalLength >= 15 then
                local len = literalLength - 15
                while len >= 255 do
                    output[#output + 1] = string.char(255)
                    len = len - 255
                end
                output[#output + 1] = string.char(len)
            end
    
            output[#output + 1] = string.sub(input, literalStart, inputLength)
        end
    end
    return table.concat(output)
end


local function escapeString(s)
	return s:gsub(".", function(c)
		local byte = string.byte(c)
		if c == "\\" then
			return "\\\\"
		elseif c == "\"" then
			return "\\\""
		elseif c == "\n" then
			return "\\n"
		elseif c == "\r" then
			return "\\r"
		elseif c == "\t" then
			return "\\t"
		elseif c == "#" then
			return "##"
		elseif byte < 32 or byte > 126 then
			return string.format("\\x%02X", byte)
		else
			return c
		end
	end)
end

local gsubColors = {
    ["#dbd700"] = true, 
    ["#CE04B6"] = true, 
    ["#40a9ff"] = true,
    ["#CE9178"] = true,
    ["#b5cea8"] = true,
    ["#569cd6"] = true,
    ["#eeeeee"] = true
}

local bracketColors = {
    "#dbd700", 
    "#CE04B6", 
    "#40a9ff"
}

local typeColors = {
    string = "#CE9178",
    number = "#b5cea8",
    boolean = "#569cd6"
}

function tableToString(tbl, indent)
    local function getBracketColor(indent)
        return bracketColors[(indent % 3) + 1]
    end

    local function getTypeColor(type)
        return typeColors[type]
    end

	indent = indent or 0
	local indentStr = string.rep("\t", indent)
	local lines = {getBracketColor(indent).."{".."#eeeeee"}
	local subIndent = indent + 1
	local subIndentStr = string.rep("\t", subIndent)

	for k, v in pairs(tbl) do
		local key
		if type(k) == "string" then
			key = getBracketColor(subIndent)..'[#CE9178"'..k..'"'..getBracketColor(subIndent)..']#eeeeee'
		else
			key = getBracketColor(subIndent).."["..getTypeColor(type(k))..tostring(k)..getBracketColor(subIndent).."]#eeeeee"
		end

		local value
		if type(v) == "table" then
			value = tableToString(v, subIndent)
		elseif type(v) == "string" then
			value = '#CE9178"' .. escapeString(v) .. '"#eeeeee'
		else
			value = getTypeColor(type(v))..tostring(v).."#eeeeee"
		end

		table.insert(lines, string.format("%s%s = %s,", subIndentStr, key, value))
	end

	table.insert(lines, string.format("%s"..getBracketColor(indent).."}", indentStr))
	return table.concat(lines, "\n")
end


function stringToTable(str)
    local pos = 1
    local len = #str

    str = str:gsub("#%x%x%x%x%x%x", function(s)
		return gsubColors[s] and "" or s
	end)

    local function peek()
        return str:sub(pos,pos)
    end

    local function nextChar()
        local c = str:sub(pos,pos)
        pos = pos + 1
        return c
    end

    local function skipWhitespace()
        while true do
            local c = peek()
            if c == " " or c == "\t" or c == "\n" or c == "\r" then
                pos = pos + 1
            else
                break
            end
        end
    end

    local function parseString()
        local result = {}
        pos = pos + 1

        while pos <= len do
            local c = nextChar()

            if c == '"' then
                return table.concat(result)
            elseif c == "\\" then
                local esc = nextChar()

                if esc == "n" then
                    table.insert(result,"\n")

                elseif esc == "r" then
                    table.insert(result,"\r")

                elseif esc == "t" then
                    table.insert(result,"\t")

                elseif esc == "\\" then
                    table.insert(result,"\\")

                elseif esc == '"' then
                    table.insert(result,'"')

                elseif esc == "x" then
                    local hex = str:sub(pos,pos+1)
                    pos = pos + 2
                    table.insert(result,string.char(tonumber(hex,16)))

                else
                    table.insert(result,esc)
                end
            else
                table.insert(result,c)
            end
        end

        error("Unclosed string")
    end

    local function parseNumber()
        local start = pos
        while str:sub(pos,pos):match("[%d%.%-]") do
            pos = pos + 1
        end
        return tonumber(str:sub(start,pos-1))
    end

    local parseValue

    local function parseKey()
        skipWhitespace()

        if nextChar() ~= "[" then
            error("Expected '[' at "..pos)
        end

        skipWhitespace()

        local key

        if peek() == '"' then
            key = parseString()
        else
            key = parseNumber()
        end

        skipWhitespace()

        if nextChar() ~= "]" then
            error("Expected ']' at "..pos)
        end

        return key
    end

    local function parseTable()
        local t = {}
        pos = pos + 1

        while true do
            skipWhitespace()

            if peek() == "}" then
                pos = pos + 1
                return t
            end

            local key = parseKey()

            skipWhitespace()

            if nextChar() ~= "=" then
                error("Expected '=' at "..pos)
            end

            skipWhitespace()

            local value = parseValue()
            t[key] = value

            skipWhitespace()

            if peek() == "," then
                pos = pos + 1
            end
        end
    end

    function parseValue()
        skipWhitespace()

        local c = peek()

        if c == "{" then
            return parseTable()

        elseif c == '"' then
            return parseString()

        elseif c:match("[%-%d]") then
            return parseNumber()

        elseif str:sub(pos,pos+3) == "true" then
            pos = pos + 4
            return true

        elseif str:sub(pos,pos+4) == "false" then
            pos = pos + 5
            return false

        elseif str:sub(pos,pos+2) == "nil" then
            pos = pos + 3
            return nil
        end

        error("Unexpected token at "..pos)
    end

    local ok, result = pcall(parseValue)
    if not ok then
        return nil, result
    end

    return result
end
