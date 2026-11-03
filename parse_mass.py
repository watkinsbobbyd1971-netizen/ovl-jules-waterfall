# If height is not present, we can't use it.
# Wait, for ships, isn't draft acceptable for bounding box height if depth isn't available?
# No, "Draft does not equal Height. Only explicitly stated displacement/mass and overall height are acceptable; otherwise, the subject must be skipped to avoid fabrication."
# (Memory: For maritime vessels (CAT_08), 'Gross Tonnage' (GT) is a volumetric measurement and cannot be used to determine mass. Additionally, 'Draft' does not equal 'Height'. Only explicitly stated displacement/mass and overall height are acceptable; otherwise, the subject must be skipped to avoid fabrication.)

# This rule is incredibly strict. I MUST only use ships with BOTH height (or depth) AND displacement (or mass) explicitly stated.
# So far I found:
# - BRP Jose Rizal (REG_06, 2019)
# - INS Vikrant (2013) (REG_06, 2013)
# - Harmony of the Seas (REG_10, 2015)
# - Allure of the Seas (REG_10, 2009/2010 -> actually it was launched 2009, completed 2010. Rule: "dated 2010-2019" - year comes from THIS subject's own source page. We can use 2010).
# - RV Sikuliaq (REG_10, 2012)
# - Titan (submersible) (REG_10, 2018)
# - DSV Alvin (acquired 1964 -> out of era)

print("Got it")
