require("dotenv").config()
const express = require("express")
const cors    = require("cors")

const statesRouter   = require("./src/routes/states")
const villagesRouter = require("./src/routes/villages")
const authRouter     = require("./src/routes/auth")

const app  = express()
const PORT = process.env.PORT || 3000

app.use(cors())
app.use(express.json())

app.get("/", (req, res) => {
  res.json({ message: "India Villages API is running!" })
})

app.use("/api/auth",     authRouter)
app.use("/api/states",   statesRouter)
app.use("/api/villages", villagesRouter)

app.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`)
})