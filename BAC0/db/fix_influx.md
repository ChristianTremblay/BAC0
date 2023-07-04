from(bucket: "BAC0")
  |> range(start: -1000d)
  |> filter(fn: (r) => r._measurement == "Device_5/binaryInput:0")
  |> map(fn: (r) => ({r with _value: if r._value == "active" then "1" else r._value} ))
  |> map(fn: (r) => ({r with _value: if r._value == "inactive" then "0" else r._value} ))

from(bucket: "BAC0")
  |> range(start: -1000d)
  |> filter(fn: (r) => r._measurement == "Device_5/binaryInput:0")
  |> map(fn: (r) => ({r with _value: int(v: r._value)} ))


  from(bucket: "BAC0")
  |> range(start: -1000d)
  |> filter(fn: (r) => r._measurement =~ /binary/ and
                       r._value =~ /inactive/
            )
  |> map(fn: (r) => ({r with _value: "0"} ))


  from(bucket: "BAC0")
  |> range(start: -1000d)
  |> filter(fn: (r) => r._measurement =~ /binary/ and
                       r._field == "_value"
            )
  |> map(fn: (r) => ({r with _value: "0"} ))


    from(bucket: "BAC0")
  |> range(start: -300d)
  |> filter(fn: (r) => r._measurement =~ /multi/ and 
                       r._field == "value"
            )
  |> map(fn: (r) => ({r with _value: int(v: r._value)} ))


  from(bucket: "BAC0")
  |> range(start: -300d)
  |> filter(fn: (r) => r._measurement =~ /multi/ and 
                       r._field == "value" and
                       r._value == ""
            )
  |> map(fn: (r) => ({r with _value: int(v: 0)} ))



# To correct an empty MSV value
  from(bucket: "BAC0")
  |> range(start: -300d)
  |> filter(fn: (r) => r._measurement =~ /multi/ and 
                       r._field == "value"
            )
  |> map(fn: (r) => ({r with _value: if r._value == "" then int(v: 0) else int(v: r._value)} ))


# To correct a MSV value of inactive
from(bucket: "BAC0")
  |> range(start: -300d)
  |> filter(fn: (r) => r._measurement =~ /multi/ and 
                       r._field == "value" and
                       r._value == "inactive
            )
  |> map(fn: (r) => ({r with _value: int(v: 0)} ))