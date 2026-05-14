# Final Resolution

Investigation artifacts preserved under `.investigation/`. Root cause: `NApplicationCard` "Edge Google" in `TO.xaml` targets `https://www.google.com/` with a loose `title='Google'` scope and no in-card navigation, so it attached to a google.ro tab where the Doodle drawer link does not exist. Apply Option A or Option B above when you're ready to edit TO.xaml.
