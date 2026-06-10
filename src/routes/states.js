const express = require("express")
const router  = express.Router()
const prisma  = require("../lib/prisma")

router.get("/", async (req, res) => {
  try {
    const states = await prisma.state.findMany({
      orderBy: { name: "asc" }
    })
    res.json({ success: true, data: states })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

router.get("/:id/districts", async (req, res) => {
  try {
    const districts = await prisma.district.findMany({
      where: { stateId: parseInt(req.params.id) },
      orderBy: { name: "asc" }
    })
    res.json({ success: true, data: districts })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

router.get("/:id/subdistricts", async (req, res) => {
  try {
    const subdistricts = await prisma.subDistrict.findMany({
      where: { districtId: parseInt(req.params.id) },
      orderBy: { name: "asc" }
    })
    res.json({ success: true, data: subdistricts })
  } catch (error) {
    res.status(500).json({ success: false, error: error.message })
  }
})

module.exports = router