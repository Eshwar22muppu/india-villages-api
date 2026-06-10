const express = require("express")
const router  = express.Router()
const prisma  = require("../lib/prisma")

router.get("/search", async (req, res) => {
  const { q } = req.query
  if (!q || q.length < 2) {
    return res.status(400).json({
      success: false,
      error: "Search query must be at least 2 characters"
    })
  }
  try {
    const results = await prisma.village.findMany({
      where: {
        name: { contains: q, mode: "insensitive" }
      },
      include: {
        subDistrict: {
          include: {
            district: {
              include: { state: true }
            }
          }
        }
      },
      take: 20
    })
    res.json({ success: true, count: results.length, data: results })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

module.exports = router