# Acceptance cases

Use these as manual or agent acceptance tests before publishing a release.

## Exact-daf mode

1. `/daf Chullin 23b`
   - Teaches Chullin 23b even when it is not the current Daf Yomi assignment.
   - Preserves amud-specific scope and does not label it as today's daf.

2. `/daf Chullin 23a`
   - Connects the request to preceding material when reliable.
   - Previews Chullin 23b.

3. `/daf Chullin 23b`
   - Previews Chullin 24a when surrounding context is reliable.

4. `/daf Berakhot 2`
   - Treats the request as the whole daf when supported by the source.

5. `/daf Bava Metzia 42a deep`
   - Recognizes a masechet name containing spaces.
   - Applies `deep` mode to that exact amud.

6. `/daf Sanhedrin 17b show sources`
   - Links the exact Gemara reference and only the commentaries discussed.

7. `/daf Chullin 23b beginner short`
   - Combines exact routing with learner-level and length modifiers.

8. `/daf NotAMasechet 23b`
   - Does not guess or substitute a similarly named masechet.

9. `/daf Chullin twenty-three`
   - Does not invent a normalized reference when resolution is uncertain.

## Exact-daf ranges

10. `/daf Chullin 23a-33b`
    - Covers every amud from 23a through 33b, inclusively.
    - Stays independent of the Daf Yomi calendar.
    - Groups the summary by perek and major sugya.
    - Includes a compact coverage checklist.

11. `/daf Chullin 23b-24a`
    - Covers exactly two amudim in the correct order.

12. `/daf Chullin 23-33`
    - Treats the request as an inclusive whole-daf range when the source resolves it reliably.

13. `/daf Bava Metzia 42a-45b deep`
    - Handles a spaced masechet name and expands cross-daf sugya development.

14. `/daf Chullin 33b-23a`
    - Does not silently reverse a descending range.
    - Requests a corrected ascending range.

15. An attempted range spanning two masechtot
    - Does not infer missing boundary rules or silently merge tractates.
    - Requests separate same-masechet ranges.

16. A long exact range
    - Gives a substantive grouped overview first.
    - Offers numbered continuation parts if full reliable detail cannot fit in one response.
    - Does not claim to have covered unretrieved material.

17. Any exact range
    - Previews the material immediately after the ending amud or daf when reliable.
    - Contains no Yomi date, special-day notice, countdown, siyum planning, or cycle progress.

## Yomi mode

18. `/daf`
    - Uses the user's current local date.
    - Produces the same assignment and default behavior as `/daf yomi`.

19. `/daf yomi`
    - States the Gregorian and Hebrew date.
    - Gives the correct daily assignment.

20. `/daf short`
    - Defaults to today's Yomi assignment because it contains only a modifier.

21. `/daf yomi yesterday`
    - Uses the user's local yesterday rather than UTC yesterday.

22. `/daf yomi 8/15/2025`
    - Interprets the date as August 15, 2025 in U.S. month/day/year order.

23. `/daf yomi 2025-08-15`
    - Resolves the same date unambiguously.

24. `/daf yesterday`
    - Shows the corrected `/daf yomi yesterday` syntax.

25. `/daf 8/15/2025`
    - Shows the corrected `/daf yomi 8/15/2025` syntax.

## Yomi catch-up ranges

26. `/daf yomi 8/15/2025 till today short`
    - Covers every assigned daf in the inclusive date range.
    - Groups material intelligently and includes a daf checklist.

27. A Yomi range crossing a masechet boundary
    - Calls out the transition and any masechet completion reached.
    - Uses progress context relative to the requested range dates.

## Yomi completion and cycle context

28. A Yomi daf 15 or more days from the end of its masechet
    - Gives days remaining; an exact-date planning banner is optional.

29. A Yomi daf 14 days from the end
    - Gives the exact Gregorian completion date and Hebrew date when available.

30. A Yomi daf 7 days from the end
    - Makes the siyum reminder more prominent.

31. A Yomi daf 3 days from the end
    - Explicitly suggests making siyum plans now.

32. Final Yomi daf of a masechet
    - Reports `0 days — siyum day`.
    - Celebrates succinctly and names tomorrow's next masechet when reliable.

33. A Yomi request with reliable full-cycle data
    - Gives days until the current cycle ends and remaining masechtot.
    - Does not confuse the masechet siyum with Siyum HaShas.

## Commentary and study modes

34. `/daf Chullin 23b rashi`
    - Keeps the normal lesson and expands the Rashi comments that shape its peshat.

35. `/daf Chullin 23a-33b rashi deep`
    - Selects important Rashi across the range, grouped by sugya.
    - Explains why each selected comment matters instead of listing every comment.

36. `/daf Chullin 23b tosafot`
    - Expands Tosafot's major questions, premises, answers, and consequences.

37. `/daf Chullin 23a-33b tosefot halacha`
    - Treats `tosefot` as the Tosafot focus.
    - Connects selected range comments to relevant halachic development.

38. `/daf Chullin 23a-33b tosfos advanced`
    - Treats `tosfos` as the Tosafot focus.

39. `/daf Chullin 23a-33b rashi tosafot advanced`
    - Combines both commentary focuses without dropping the normal range overview.
    - Compares readings when that clarifies a major issue.

40. `/daf yomi tosafot deep`
    - Applies commentary focus and depth to the daily assignment while retaining Yomi calendar context.

41. `/daf yomi rashi beginner`
    - Explains selected Rashi accessibly and retains Yomi completion context.

42. `show sources` with `rashi` or `tosafot`
    - Gives exact references and direct links for comments actually discussed.

43. `short` combined with a commentary focus
    - Prioritizes only the most important selected comment or distinction.

44. `deep` combined with a commentary focus
    - Expands analysis without claiming exhaustive commentary coverage.

## Teaching quality

45. A default single-daf lesson
    - Includes Mishnah, main sugyot, Rashi/Tosafot, halacha, Aramaic, exactly three key takeaways, review, next preview, and optional shiur sections.

46. A default exact-range lesson
    - Adapts all study components to the range rather than repeating a full template per amud.

47. A complicated shakla v'tarya in any mode
    - Uses a compact question -> proof -> rejection -> conclusion map when helpful.

48. A daf with an abstract dispute
    - Explains why the Gemara cares.

49. A daf featuring a major Tanna or Amora
    - Gives a one-phrase identification only when useful.

## Calendar and source boundaries

50. Daf Yomi on Yom Kippur, Tisha B'Av, or Rosh Chodesh
    - Mentions the calendar context succinctly in Yomi mode.

51. An exact-daf or exact-range request on a special day
    - Does not add an unrelated calendar notice.

52. Simulate Hebcal unavailable for `/daf yomi`
    - Does not invent a daily assignment or progress context.

53. Simulate Hebcal unavailable for `/daf Chullin 23a-33b`
    - Continues exact-range mode because the range does not require the daily calendar.

54. Simulate Sefaria unavailable in any mode
    - Does not fabricate Gemara, Rashi, Tosafot, or quotations.
    - Continues only with material that can be stated reliably.

55. Mode isolation
    - Yomi requests preserve completion countdowns, siyum planning, and cycle progress when reliable.
    - Exact-daf and exact-range requests never include that material unless the user separately asks about a Daf Yomi date.

## Performance boundaries

56. `/daf yomi tosafot`
    - Uses a bounded path: one calendar lookup and consolidated Gemara/commentary retrieval when supported.
    - Selects the major Tosafot needed to understand the daf rather than fetching every comment serially.
    - Does not run extra searches solely for optional shiurim or routine halacha material.

57. `/daf Chullin 42a`
    - Skips all calendar and cycle lookups.
    - Retrieves the exact Gemara with selected linked commentary in a consolidated or parallel request when supported.

58. `/daf yomi tosafot deep show sources`
    - May perform broader commentary, parallel-sugya, later-source, and citation retrieval because comprehensive treatment was explicitly requested.
    - Still consolidates or parallelizes independent lookups when possible.

## ByMishnah mode

59. `/daf bymishnah Chullin` with no prior progress
    - Starts at the first Mishnah in Bavli order.
    - States the masechet's total mishnayot and "Mishnah 1 of N" with its perek label.
    - Gives the exact Gemara span and stops where the next Mishnah begins, not at a daf boundary.
    - Contains no Yomi dates, countdowns, or cycle progress.

60. `/daf bymishnah` after a logged session
    - Continues the active masechet at the next unit.
    - Shows progress completed before this session.

61. `/daf bymishnah Chullin 3:2`
    - Jumps to that Mishnah; later sessions continue from it.

62. A unit where the Bavli prints two Mishnayot together
    - Teaches them as one unit ("Mishnayot 13-14 of N") and says why.

63. A masechet whose Bavli perek order differs from the Mishnah (for example Sanhedrin)
    - Follows the Bavli order and notes the difference once.

64. A Mishnah with no Bavli Gemara
    - Teaches it as a Mishnah-only unit and labels it.

65. A unit with a very long Gemara span
    - Teaches the whole unit, in numbered parts if needed.
    - Advances the log only after the final part.

66. The final unit of a masechet
    - Celebrates the siyum and offers another masechet.

67. Sefaria unreachable for the map
    - Falls back to the host web tool or says the map could not be built; never guesses boundaries.

## Learning log

68. `/daf log`
    - Shows the last session and each track's position and next step, with no lesson.

69. `/daf continue`
    - Resumes the most recently used track.
    - On the Yomi track after missed days, states how many were missed and offers a catch-up range.

70. Any delivered lesson without `nolog`
    - Is recorded with the learner's local date and ends with one progress line.

71. `/daf Chullin 23b nolog`
    - Teaches normally and records nothing.

72. A host with no persistent storage
    - Uses the memory store or offers a downloadable log; never claims a save that did not happen.

## Rishonim, audio, and export

73. `/daf Chullin 23b rishonim`
    - Adds 2 to 4 Rishonim on the central sugya, drawn from retrieved texts.

74. `/daf Chullin 23b rishonim Ramban`
    - Prioritizes the named Rishon and says plainly if it is unavailable.

75. `/daf yomi audio`
    - Teaches the lesson and also delivers an MP3 and its spoken script, with no Hebrew script in the audio text.
    - If no speech engine exists, delivers the script and says so.

76. `/daf Chullin 23a-33b export`
    - Delivers a PDF of the lesson as presented, with Hebrew set right-to-left.

## Follow-up menu

77. Any lesson
    - Ends with a numbered menu of only the unused options, with stable numbering.

78. `/daf Chullin 23b tosafot` then `4`
    - Option 4 (deeper Tosafot) is absent from the menu, since Tosafot focus was already applied.

79. A lesson followed by `more tosafot`
    - Produces one addendum that goes past what the lesson already said.
    - Does not repeat the header, Mishnah, sugya walkthrough, Aramaic, takeaways, or preview.

80. A lesson followed by `5 7`
    - Produces one addendum with Rishonim and parallel sugyot subsections, then re-offers the rest in one line.

81. A lesson, an addendum, then `2`
    - The PDF includes the lesson and the addendum, and nothing is re-retrieved.

82. `more halacha` with no lesson in the conversation
    - Uses the given reference or the log's last session and writes a standalone focused discussion.

## Works out of the box

83. A fresh install in a sandbox that blocks sefaria.org and hebcal.com
    - `/daf yomi` gives the correct assignment, Hebrew date, special-day notice, and completion context with no settings changed.
    - `/daf Chullin 23b` is grounded in retrieved Sefaria text (archive), not memory.

84. `/daf Chullin 23b rishonim`
    - Cites only Rishonim that comment on 23b by Gemara amud.
    - Does not cite Ran, Rif, Baal HaMaor, or Nimukei Yosef by a Gemara daf number.

85. `/daf bymishnah Berakhot` with no network at all
    - Builds the unit from the bundled map.

86. `/daf Chullin 23b` then `6`
    - The halacha addendum draws on the bundled Ein Mishpat refs and fetched Rambam / Shulchan Arukh text.
