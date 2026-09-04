dofile("Bitstream.lua")
dofile("Modules.lua")

local readUserdataTbl = {
    [10001] = "Uuid",
    [10003] = "Vec3",
    [10004] = "Quat",
    [10005] = "Color",
    [10021] = "Shape",
    [10022] = "Body",
    [10023] = "Interactable",
    [10024] = "Container",
    [10025] = "Harvestable",
    [10027] = "World",
    [10030] = "Player",
    [10031] = "Character",
    [10032] = "Joint",
    [10036] = "Portal",
    [10037] = "PathNode",
    [10038] = "Lift",
    [10039] = "ScriptableObject",
    [20002] = "Tool",
}

local function getTableSize(data)
    local size = 0
    
    for _ in pairs(data) do
        size = size + 1
    end

    return size
end

local function isArray(tbl)
    local hasLooped
    local keys = {}

    for k, _ in pairs(tbl) do
        hasLooped = true
        if type(k) ~= "number" or k % 1 ~= 0 then
            return false
        end
        table.insert(keys, k)
    end

    if not hasLooped then return false end

    table.sort(keys)

    for i = 2, #keys do
        if keys[i] ~= keys[i - 1] + 1 then
            return false
        end
    end

    return true
end

local function getFirstIndex(tbl)
    for i in pairs(tbl) do return i end
end

local function binaryToHex(inputStr)
    local hex = {}

    for i = 1, #inputStr do
        table.insert(hex, string.format("%02X", string.byte(inputStr, i)))
    end

    return table.concat(hex, " ")
end

function decodeBitstream(data, isBin)
    if not isBin then
        data = decodeLZ4(decodeBase64(data))
    end

    local stream = BitStream.new(data)
    local magic = stream:readBytes(3)
    local version = stream:readUInt(32)

    local function parseObject()
        local typeId = stream:readByte()

        if typeId == 0 or typeId == 1 or typeId == 101 then
            return nil
        elseif typeId == 2 then
            return stream:readBits(1) ~= 0
        elseif typeId == 3 then
            return stream:readFloat()
        elseif typeId == 4 then
            local size = stream:readUInt(32)
            stream:align()
            return stream:readBytes(size)
        elseif typeId == 5 then
            local totalElements = stream:readUInt(32)
            local isArray = stream:readBits(1) == 1
            local result = {}

            if isArray then
                local offset = stream:readUInt(32)
                for i = offset, offset + totalElements - 1 do
                    result[i] = parseObject()
                end
            else
                for _ = 1, totalElements do
                    local key = parseObject()
                    local value = parseObject()
                    result[key] = value
                end
            end

            return result
        elseif typeId == 6 then
            return bit.tobit(stream:readInt(32))
        elseif typeId == 7 then
            return bit.tobit(stream:readInt(16))
        elseif typeId == 8 then
            return stream:readByte()
        elseif typeId == 100 then
            local userdata = {}
            local userdataId = stream:readUInt(32)

            userdata.data = {}
            userdata.userdataId = userdataId
            userdata.userdataType = readUserdataTbl[userdataId]

            if userdataId == 10004 or userdataId == 10005 then
                for i = 1, 4 do
                    userdata.data[i] = stream:readFloat()
                end
            elseif userdataId == 10003 then
                for i = 1, 3 do
                    userdata.data[i] = stream:readFloat()
                end
            elseif userdataId == 10001 then
                userdata.data[1] = stream:readUInt(128)
            else
                userdata.data[1] = stream:readUInt(32)
            end

            return userdata
        end
    end

    local ok, content = pcall(function()
        return parseObject()
    end)

    if ok then
        return {
            magic = magic,
            version = version,
            content = content,
        }
    else
        return nil, content
    end
end


function encodeBitstream(data)
    local stream = BitStream.new()

    stream:writeBytes(data.magic)
    stream:writeUInt(data.version, 32)

    local function writeObject(data)
        local dataType = type(data)

        local function writeUserdata(userdata)
            local userdataId = userdata.userdataId
            local userdataData = userdata.data

            stream:writeByte(100)
            stream:writeUInt(userdataId, 32)

            if userdataId == 10004 or userdataId == 10005 then -- Quat or Color
                for i = 1, 4 do
                    stream:writeFloat(userdataData[i])
                end
            elseif userdataId == 10003 then -- Vec3
                for i = 1, 3 do
                    stream:writeFloat(userdataData[i])
                end
            elseif userdataId == 10001 then -- Uuid
                stream:writeUInt(userdataData[1], 128)
            else
                stream:writeUInt(userdataData[1], 32)
            end
        end

        if dataType == "nil" then
            stream:writeByte(1)
            return
        elseif dataType == "boolean" then
            stream:writeByte(2)
            stream:writeBits(data and 1 or 0, 1)
        elseif dataType == "number" then
            local isInteger = data == math.floor(data)
    
            if isInteger then
                local absVal = math.abs(data)

                if absVal <= 32767 then
                    if absVal <= 127 then
                        stream:writeByte(8)
                        stream:writeInt(data, 8)
                    else
                        stream:writeByte(7)
                        stream:writeInt(data, 16)
                    end
                else
                    stream:writeByte(6)
                    stream:writeInt(data, 32)
                end
            else
                stream:writeByte(3)
                stream:writeFloat(data)
            end
        elseif dataType == "string" then
            stream:writeByte(4)
            stream:writeUInt(#data, 32)
            stream:align()
            stream:writeBytes(data)
        elseif dataType == "table" then
            if data.userdataType and data.userdataId then
                writeUserdata(data)
                return
            end

            stream:writeByte(5)
        
            local tableSize = getTableSize(data)
            local tableIsArray = isArray(data)
            
            stream:writeUInt(tableSize, 32)
            stream:writeBits(tableIsArray and 1 or 0, 1)

            if tableIsArray then
                stream:writeUInt(getFirstIndex(data) or 1, 32)
        
                for _, v in pairs(data) do
                    writeObject(v)
                end
            else
                for key, val in pairs(data) do
                    writeObject(key)
                    writeObject(val)
                end
            end
        end
    end

    local ok, err = pcall(function()
        writeObject(data.content)
    end)

    if ok then
        return encodeBase64(encodeLZ4(stream:tostring()))
    else
        return nil, err
    end
end


