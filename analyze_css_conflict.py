"""Analyze CSS conflicts affecting shape positioning"""

print("CSS CONFLICT ANALYSIS")
print("=" * 50)
print()

print("TEMPLATE INLINE STYLES:")
print("1. Container: style='position: relative; text-align: center; padding: 40px 0;'")
print("2. Input fields: style='position: absolute; bottom: Xpx; left: calc(50% + Ypx)'")
print()

print("CSS OVERRIDES FOUND:")
print("1. General .shape-diagram-with-input:")
print("   - position: relative")
print("   - display: flex")
print("   - justify-content: center")
print("   - margin: 20px 0")
print("   - background: #f9f9f9")
print()

print("2. Expanded row .expanded-row .shape-diagram-with-input:")
print("   - margin: 0")
print("   - padding: 0 !important")
print("   - display: inline-block")
print("   - line-height: 0")
print("   - position: relative")
print()

print("3. Override for padding: .expanded-row .shape-diagram-with-input[style*='padding']:")
print("   - padding: 0 !important")
print()

print("PROBLEM IDENTIFIED:")
print("The CSS is forcing padding: 0 !important on expanded rows")
print("But our template calculations assume padding: 40px 0")
print("This changes the container reference point!")
print()

print("IMPACT ON POSITIONING:")
print("- Template calculation assumes 40px top/bottom padding")
print("- CSS forces padding to 0px in expanded rows")
print("- This shifts all positioning upward by ~40px")
print("- Input fields appear 'too high' because container is smaller")
print()

print("SOLUTIONS:")
print("1. Modify the CSS to preserve template padding")
print("2. Adjust template calculations for expanded row context")
print("3. Use different positioning logic when in expanded rows")
print()

print("RECOMMENDATION:")
print("Check if this template is being used in an expanded row context")
print("where the CSS padding override is being applied.")