const express  = require("express")
const router   = express.Router()
const bcrypt   = require("bcryptjs")
const jwt      = require("jsonwebtoken")
const crypto   = require("crypto")
const prisma   = require("../lib/prisma")

router.post("/register", async (req, res) => {
  const { email, password } = req.body
  try {
    const hashed = await bcrypt.hash(password, 12)
    const user = await prisma.user.create({
      data: { email, password: hashed }
    })
    res.json({ success: true, message: "User registered", userId: user.id })
  } catch (error) {
    res.status(400).json({ success: false, error: "Email already exists" })
  }
})

router.post("/login", async (req, res) => {
  const { email, password } = req.body
  try {
    const user = await prisma.user.findUnique({ where: { email } })
    if (!user) return res.status(401).json({ error: "Invalid credentials" })
    const valid = await bcrypt.compare(password, user.password)
    if (!valid) return res.status(401).json({ error: "Invalid credentials" })
    const token = jwt.sign(
      { userId: user.id },
      process.env.JWT_SECRET,
      { expiresIn: "7d" }
    )
    res.json({ success: true, token })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

router.post("/generate-key", async (req, res) => {
  const authHeader = req.headers["authorization"]
  if (!authHeader) return res.status(401).json({ error: "No token provided" })
  const token = authHeader.split(" ")[1]
  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET)
    const key        = crypto.randomBytes(16).toString("hex")
    const secret     = crypto.randomBytes(32).toString("hex")
    const secretHash = await bcrypt.hash(secret, 12)
    await prisma.apiKey.create({
      data: { key, secretHash, userId: decoded.userId }
    })
    res.json({
      success: true,
      key,
      secret,
      message: "Save your secret now — it will not be shown again!"
    })
  } catch (error) {
    res.status(401).json({ error: "Invalid token" })
  }
})

module.exports = router