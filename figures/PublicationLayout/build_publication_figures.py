"""Build the nine TRACE-PHENO figures with bold typography and compact panels."""
import sys
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from layout_common import canvas, panel, diagram, box, arrow, grid, export
from layout_common import read_csv, P, STATUS, CAPABILITY, REVISION, DATA, OLD_SOURCE


def heading(fig, text):
    top = 1 - 4 / (fig.get_size_inches()[1] * 72)
    fig.text(.5, top, text, ha='center', va='top', fontsize=12)


def figure1():
    fig = canvas(5.4)
    heading(fig, 'TRACE-PHENO study design and sampling')
    ax = diagram(fig, (.015, .67, .97, .255), 'A', 'Measurement pathway')
    labels = ['Evidence\navailability', 'Phenotype\ndefinition', 'Cohort\nmembership', 'Outcome\nestimate']
    xs = [.005, .26, .515, .77]
    fills = ['#EAF2F8', '#E8F5E9', '#FFF4E6', '#FDEDEC']
    edges = ['#4C78A8', '#2A9D8F', '#E69F00', '#D55E00']
    for i, (x, label) in enumerate(zip(xs, labels)):
        box(ax, x, .30, .225, .60, label, fc=fills[i], ec=edges[i], fs=10)
        if i < 3:
            arrow(ax, (x + .23, .60), (xs[i + 1] - .006, .60))
    ax.text(.5, .05, 'Unavailable evidence remains unknown', ha='center', va='center', fontsize=9.5, color='#8C4A00')

    ax = diagram(fig, (.015, .02, .43, .63), 'B', 'Five database contexts')
    contexts = [('MIMIC', 'Reference + downstream'), ('eICU', 'Multi-hospital transport'),
                ('NWICU', 'Structured-data application'), ('SICdb', 'Small-sample application'),
                ('HiRID', 'AP codes unavailable')]
    for i, (database, role) in enumerate(contexts):
        box(ax, .005, .804 - i * .195, .99, .17, f'{database}\n{role}', fs=10)

    ax = diagram(fig, (.475, .02, .51, .63), 'C', 'MIMIC sample flow')
    box(ax, .005, .815, .99, .17, 'Downstream summaries\n546,028 admissions', fc='#EAF2F8', ec=P['P0'], fs=10)
    box(ax, .005, .51, .99, .27, 'Separate reference sampling frame\n223,452 patients\n900 representative encounters', fs=9.5)
    box(ax, .005, .265, .99, .17, '900 sampled = 100 pilot + 800 formal\n800 formal = 560 development + 240 validation', fs=9.1)
    box(ax, .005, .015, .99, .19, '240 validation → 86 strict\n20 definitive AP + 66 non-AP\n154 probable or indeterminate', fc='#FFF4E6', ec=P['P2'], fs=9.5)
    export(fig, 'Figure_1_Study_Design')


def figure2():
    labels = read_csv(OLD_SOURCE, 'fig2_reference_distribution.csv')
    names = {'definitive_AP': 'Definitive AP', 'probable_AP': 'Probable AP', 'non_AP': 'Non-AP', 'indeterminate': 'Indeterminate'}
    colors = {'definitive_AP': P['P3'], 'probable_AP': P['P2'], 'non_AP': P['P0'], 'indeterminate': '#929AA2'}
    fig = canvas(5.15)
    heading(fig, 'AP construct and reference labels')
    ax = diagram(fig, (.015, .035, .345, .89), 'A', 'Atlanta criteria')
    content = ['1  Compatible abdominal\npain', '2  Lipase or amylase\n≥3× local ULN', '3  Characteristic imaging']
    for y, text, fc, ec in zip([.71, .415, .12], content,
                               ['#EAF2F8', '#FFF4E6', '#FDEDEC'], ['#4C78A8', '#E69F00', '#D55E00']):
        box(ax, .005, y, .99, .22, text, fs=10, fc=fc, ec=ec)
    ax.text(.5, .035, 'At least 2 findings', ha='center', va='center', fontsize=10)
    ax = panel(fig, (.385, .48, .60, .445), 'B', 'Reference labels (n=900)', margins=(82, 31, 20, 30))
    order = ['definitive_AP', 'probable_AP', 'non_AP', 'indeterminate']
    # The frozen source table supplies the four full-hospitalization counts.
    label_column = 'reference_label' if 'reference_label' in labels.columns else labels.columns[0]
    count_column = 'n' if 'n' in labels.columns else labels.columns[1]
    values = labels.set_index(label_column).loc[order, count_column].astype(int).to_numpy()
    ax.barh(np.arange(4), values, height=.64, color=[colors[x] for x in order])
    ax.set_yticks(np.arange(4), [names[x] for x in order])
    ax.invert_yaxis()
    ax.set_xlim(0, 420)
    ax.set_xticks([0, 100, 200, 300, 400])
    ax.set_xlabel('Encounters')
    grid(ax)
    for y, value in enumerate(values):
        ax.text(value + 9, y, str(value), va='center', fontsize=10)
    ax = panel(fig, (.385, .035, .60, .415), 'C', 'Indeterminate by evidence window', margins=(89, 54, 15, 32), title_size=10.4)
    counts = [334, 869]
    ax.barh(np.arange(2), counts, color=['#929AA2', P['P3']], height=.54)
    ax.set_yticks([0, 1], ['Full\nhospitalization', 'First 24 hours'])
    ax.invert_yaxis()
    ax.set_xlim(0, 1120)
    ax.set_xticks([0, 300, 600, 900])
    ax.set_xlabel('Indeterminate encounters (of 900)', fontsize=9.5)
    grid(ax)
    for y, value in enumerate(counts):
        ax.text(value + 22, y, f'{value}/900', va='center', fontsize=9.5)
    ax.set_xlabel('Indeterminate encounters (of 900)\nFirst 24 hours: 31 classifiable encounters', fontsize=9.3, linespacing=1.5)
    export(fig, 'Figure_2_Construct_and_Reference')


def figure3():
    metrics = read_csv(REVISION, 'BENCHMARK_METRICS.csv')
    boundary = read_csv(REVISION, 'BOUNDARY_INTERVALS.csv')
    policies_data = read_csv(DATA, 'Figure_3_Label_Boundary.csv')
    fig = canvas(5.9)
    heading(fig, 'Conditional agreement for P0–P2')
    strict = metrics[(metrics.policy == 'strict') & (metrics.scale == 'design_weighted')]
    boundary_strict = boundary[(boundary.policy == 'strict') & (boundary.scale == 'design_weighted')]
    for rect, letter, metric, title, limits, ticks in [
        ((.015, .53, .475, .395), 'A', 'sensitivity', 'Sensitivity', (0, .55), [0, .1, .2, .3, .4, .5]),
        ((.515, .53, .47, .395), 'B', 'specificity', 'Specificity', (.9, 1.012), [.90, .95, 1.00]),
    ]:
        ax = panel(fig, rect, letter, title, margins=(31, 42, 10, 29))
        base = strict[strict.metric == metric].set_index('phenotype')
        fix = boundary_strict[boundary_strict.metric == metric].set_index('phenotype')
        for i, phenotype in enumerate(['P0', 'P1', 'P2']):
            row = base.loc[phenotype]
            interval = fix.loc[phenotype] if phenotype == 'P2' and metric == 'specificity' else row
            est, lo, hi = float(row.estimate), float(interval.ci_lower), float(interval.ci_upper)
            ax.errorbar(est, i, xerr=[[est - lo], [hi - est]], fmt='o', color=P[phenotype], markersize=5.5, capsize=3, lw=1.6)
        ax.set_yticks([0, 1, 2], ['P0', 'P1', 'P2'])
        ax.set_ylim(2.4, -.4)
        ax.set_xlim(*limits)
        ax.set_xticks(ticks)
        ax.set_xlabel('Design-weighted estimate\n(95% CI)')
        grid(ax)
    ax = panel(fig, (.015, .06, .97, .445), 'C', 'Sensitivity under reference-label policies', margins=(53, 45, 13, 30))
    policies = ['strict', 'probable_positive', 'probable_negative', 'all_uncertain_positive', 'all_uncertain_negative']
    labels = ['Strict', 'Probable\npositive', 'Probable\nnegative', 'All uncertain\npositive', 'All uncertain\nnegative']
    offsets = {'P0': -.16, 'P1': 0, 'P2': .16}
    for phenotype in ['P0', 'P1', 'P2']:
        sub = policies_data[(policies_data.phenotype == phenotype) & (policies_data.scale == 'design_weighted') & (policies_data.metric == 'sensitivity')].set_index('policy').loc[policies]
        ax.scatter(np.arange(5) + offsets[phenotype], sub.estimate.to_numpy(float), color=P[phenotype], s=36, zorder=3)
    ax.set_xticks(np.arange(5), labels)
    ax.set_xlim(-.5, 4.5)
    ax.set_ylim(0, .14)
    ax.set_yticks([0, .04, .08, .12])
    ax.set_ylabel('Design-weighted sensitivity')
    grid(ax, 'y')
    handles = [plt.Line2D([], [], marker='o', linestyle='', color=P[x], markersize=5) for x in ['P0', 'P1', 'P2']]
    fig.legend(handles, ['P0 any-position code', 'P1 principal-position code', 'P2 code + enzyme ≥3× local ULN'], ncol=3, loc='lower center', bbox_to_anchor=(.5, .001), columnspacing=.9, handletextpad=.35, handlelength=.8, fontsize=9)
    export(fig, 'Figure_3_Conditional_Agreement')


def figure4():
    transport = read_csv(REVISION, 'TRANSPORT_COMPUTABILITY.csv')
    retention = read_csv(REVISION, 'P0_TO_P2_RETENTION.csv')
    capability = read_csv(OLD_SOURCE, 'fig4_capabilities.csv').set_index('database')
    capability.loc['MIMIC', 'imaging'] = 'partial'
    reportability = read_csv(DATA, 'Figure_5_Reportability.csv')
    databases = ['MIMIC', 'eICU', 'NWICU', 'SICdb', 'HiRID']
    status_rows = {'MIMIC': ['direct', 'direct', 'direct'], 'eICU': ['adapted', 'partial', 'proxy'],
                   'NWICU': ['direct', 'partial', 'direct'], 'SICdb': ['partial', 'direct', 'not-computable'],
                   'HiRID': ['not-identifiable'] * 3}
    fig = canvas(7.6)
    heading(fig, 'Transportability and evidence availability')
    ax = panel(fig, (.015, .565, .46, .36), 'A', 'Implementation status', margins=(42, 24, 3, 30), title_size=10.6)
    levels = list(STATUS)
    mat = np.array([[levels.index(value) for value in status_rows[db]] for db in databases])
    ax.imshow(mat, aspect='auto', cmap=mpl.colors.ListedColormap([STATUS[x] for x in levels]), vmin=-.5, vmax=len(levels) - .5)
    ax.set_xticks(range(3), ['P0', 'P1', 'P2'])
    ax.set_yticks(range(5), databases)
    for i, db in enumerate(databases):
        for j, value in enumerate(status_rows[db]):
            ax.text(j, i, value.replace('-', '\n'), ha='center', va='center', fontsize=9.3, color='white' if value == 'not-identifiable' else '#17212B', linespacing=1.05)
    matrix_grid(ax, 3, 5)
    ax = panel(fig, (.505, .565, .48, .36), 'B', 'Evidence capability', margins=(38, 24, 2, 30), title_size=10.6)
    fields = ['diagnosis', 'diagnosis_position', 'ULN', 'pain_semantics', 'imaging']
    values = capability.loc[databases, fields].astype(str)
    levels = list(CAPABILITY)
    mat = np.array([[levels.index(value) for value in row] for row in values.to_numpy()])
    ax.imshow(mat, aspect='auto', cmap=mpl.colors.ListedColormap([CAPABILITY[x] for x in levels]), vmin=-.5, vmax=len(levels) - .5)
    ax.set_xticks(range(5), ['Diagnosis', 'Position', 'ULN', 'Pain', 'Imaging'])
    ax.tick_params(axis='x', labelsize=8.8)
    ax.set_yticks(range(5), databases)
    for i in range(5):
        for j in range(5):
            ax.text(j, i, values.iloc[i, j], ha='center', va='center', fontsize=9.2)
    matrix_grid(ax, 5, 5)

    ax = panel(fig, (.015, .335, .97, .205), 'C', 'P0 records retained by P2', margins=(105, 30, 10, 30))
    rows = retention.set_index('context').loc[['eICU', 'NWICU']]
    keep = 100 * rows.p0_to_p2_retention.to_numpy(float)
    ax.barh([0, 1], keep, height=.57, color='#4C78A8')
    ax.barh([0, 1], 100 - keep, left=keep, height=.57, color='#D9DEE2')
    ax.set_yticks([0, 1], ['eICU · P2 proxy', 'NWICU · P2 direct'])
    ax.set_ylim(1.45, -.45)
    ax.set_xlim(0, 100)
    ax.set_xticks([0, 20, 40, 60, 80, 100])
    ax.set_xlabel('Share of P0-positive records (%)')
    for i, row in enumerate(rows.itertuples()):
        value = 100 * row.p0_to_p2_retention
        ax.text(value / 2, i, f'{int(row.p2_n)}/{int(row.p0_n)} · {value:.1f}%', ha='center', va='center', fontsize=9.8, color='white')
        ax.text(value + (100 - value) / 2, i, f'{int(row.p0_excluded_after_p2)} fewer · {100-value:.1f}%', ha='center', va='center', fontsize=9.2, color='#263238')
    ax = panel(fig, (.015, .02, .51, .29), 'D', 'Phenotype-positive\nrecords', margins=(85, 32, 18, 43))
    selection = [('eICU', 'P0', 'eICU P0', 'adapted'), ('eICU', 'P1', 'eICU P1', 'partial'),
                 ('eICU', 'P2_proxy', 'eICU P2 proxy', 'proxy'), ('NWICU', 'P0', 'NWICU P0', 'direct'),
                 ('NWICU', 'P2', 'NWICU P2', 'direct'), ('SICdb', 'P1', 'SICdb P1', 'direct')]
    counts = []
    for database, phenotype, label, status in selection:
        row = transport[(transport.context == database) & (transport.phenotype == phenotype)].iloc[0]
        counts.append((label, int(row.positive_yield), STATUS[status]))
    counts.reverse()
    bars = ax.barh(range(6), [x[1] for x in counts], height=.57, color=[x[2] for x in counts])
    ax.set_yticks(range(6), [x[0] for x in counts])
    ax.invert_yaxis()
    ax.set_xlim(0, 790)
    ax.set_xticks([0, 200, 400, 600])
    ax.set_xlabel('Positive records')
    grid(ax)
    for bar, (_, value, _) in zip(bars, counts):
        ax.text(value + 14, bar.get_y() + bar.get_height() / 2, str(value), va='center', fontsize=9.5)
    ax = panel(fig, (.555, .02, .43, .29), 'E', 'eICU hospitals with\n≥10 positive records', margins=(49, 32, 15, 43))
    rows = reportability.set_index('phenotype').loc[['P0', 'P1', 'P2-proxy']]
    values = rows.reportable_hospitals.astype(int).to_numpy()
    bars = ax.barh(range(3), values, height=.56, color=[P['P0'], P['P1'], STATUS['proxy']])
    ax.set_yticks(range(3), ['P0', 'P1', 'P2 proxy'])
    ax.invert_yaxis()
    ax.set_xlim(0, 15.5)
    ax.set_xticks([0, 5, 10, 15])
    ax.set_xlabel('Hospitals', fontsize=9.3)
    grid(ax)
    for bar, value in zip(bars, values):
        ax.text(value + .35, bar.get_y() + bar.get_height() / 2, str(value), va='center', fontsize=10)
    export(fig, 'Figure_4_Transportability')


def matrix_grid(ax, columns, rows):
    ax.set_xticks(np.arange(-.5, columns, 1), minor=True)
    ax.set_yticks(np.arange(-.5, rows, 1), minor=True)
    ax.grid(which='minor', color='white', linewidth=1.1)
    ax.tick_params(which='minor', bottom=False, left=False)


def figure5():
    burden = read_csv(DATA, 'Figure_5_Burden.csv').set_index('phenotype')
    decomposition = read_csv(DATA, 'Figure_5_Set_Decomposition.csv')
    drift = read_csv(REVISION, 'MIMIC_PAIRED_DOWNSTREAM_BOOTSTRAP.csv')
    fig = canvas(6.8)
    heading(fig, 'Selected cohorts and observed outcomes')
    ax = panel(fig, (.015, .515, .475, .41), 'A', 'MIMIC cohort size\nand deaths', margins=(44, 27, 12, 42))
    rows = burden.loc[['P0', 'P1', 'P2']]
    bars = ax.bar(range(3), rows.admissions.astype(int), width=.60, color=[P[x] for x in rows.index])
    ax.set_xticks(range(3), rows.index)
    ax.set_ylim(0, 4900)
    ax.set_yticks([0, 1000, 2000, 3000, 4000])
    ax.set_ylabel('Admissions')
    grid(ax, 'y')
    for bar, (_, row) in zip(bars, rows.iterrows()):
        ax.text(bar.get_x() + bar.get_width() / 2, row.admissions + 110,
                f'{int(row.admissions):,}\n{int(row.deaths)} deaths\n{row.mortality_pct:.2f}%', ha='center', va='bottom', fontsize=9.6, linespacing=1.05)
    ax = diagram(fig, (.515, .515, .47, .41), 'B', 'Set membership')
    p01 = decomposition[decomposition.comparison == 'P0 vs P1'].set_index('set_component')
    p03 = decomposition[decomposition.comparison == 'P0 vs P3'].set_index('set_component')
    ax.text(.01, .945, 'P0 vs P1', fontsize=10, va='center')
    box(ax, .005, .64, .475, .225, f"Both P0 and P1\n{int(p01.loc['both/P1', 'n']):,}", fc='#EAF2F8', ec=P['P1'], fs=10)
    box(ax, .52, .64, .475, .225, f"P0-only\n{int(p01.loc['P0-only secondary-position', 'n']):,}", ec=P['P0'], fs=10)
    ax.text(.01, .51, 'P0 vs P3', fontsize=10, va='center')
    for x, key, label, color in [(.005, 'both', 'Both', P['P0']), (.345, 'P0-only', 'P0-only', '#929AA2'), (.685, 'P3-only', 'P3-only', P['P3'])]:
        box(ax, x, .17, .31, .245, f"{label}\n{int(p03.loc[key, 'n']):,}", ec=color, fs=10)
    ax = panel(fig, (.015, .04, .475, .45), 'C', 'Position groups: observed outcomes', margins=(44, 43, 8, 32), title_size=10.4)
    one = p01.loc['both/P1']
    two = p01.loc['P0-only secondary-position']
    x = np.arange(2)
    mortality = ax.bar(x - .21, [one.mortality_pct, two.mortality_pct], width=.36, color=P['P3'], label='Mortality')
    icu = ax.bar(x + .21, [one.icu_pct, two.icu_pct], width=.36, color='#4C78A8', label='ICU use')
    ax.set_xticks(x, ['Principal AP\nn=1,825', 'Secondary only\nn=1,441'])
    ax.set_ylabel('Observed percent')
    ax.set_ylim(0, 42)
    ax.set_yticks([0, 10, 20, 30, 40])
    ax.legend(ncol=2, loc='upper left', columnspacing=.7, handlelength=1.1, handletextpad=.3, fontsize=9.2)
    grid(ax, 'y')
    for bars in [mortality, icu]:
        for bar in bars:
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height() + .9, f'{bar.get_height():.2f}%', ha='center', fontsize=9.4)
    ax = panel(fig, (.515, .04, .47, .45), 'D', 'Descriptive mortality differences', margins=(57, 47, 8, 32), title_size=10.4)
    order = ['P1_minus_P0', 'P2_minus_P0', 'P3_minus_P0', 'P3_minus_P2']
    rows = drift.set_index('comparison').loc[order]
    ax.axvspan(-1, 1, color='#D9DEE2', alpha=.55, zorder=0)
    ax.axvline(0, color='#3E4851', lw=1.1, zorder=1)
    for y, (name, row) in enumerate(rows.iterrows()):
        color = P['P1'] if name == 'P1_minus_P0' else P['P2'] if name == 'P2_minus_P0' else '#8B6F82'
        est, lo, hi = [100 * float(row[key]) for key in ['point_difference_B_minus_A', 'ci_lower', 'ci_upper']]
        ax.errorbar(est, y, xerr=[[est - lo], [hi - est]], fmt='o', color=color, markersize=5.5, capsize=3, lw=1.6)
    ax.set_yticks(range(4), ['P1 − P0', 'P2 − P0', 'P3 − P0', 'P3 − P2'])
    ax.set_ylim(3.6, -.65)
    ax.set_xlim(-4.3, 2.5)
    ax.set_xticks([-4, -2, 0, 2])
    ax.set_xlabel('Mortality difference\n(percentage points)')
    ax.text(.98, .98, 'Shaded: ±1 pp', transform=ax.transAxes, ha='right', va='top', fontsize=9.2)
    grid(ax)
    export(fig, 'Figure_5_Downstream_Consequences')


def figure6():
    fig = canvas(3.7)
    heading(fig, 'Application workflow and software reuse')
    ax = diagram(fig, (.015, .49, .97, .435), 'A', 'Application workflow')
    labels = ['Clinical\ndefinition', 'Source evidence\nand mapping', 'Phenotype\nrules', 'Cohort and\noutcome summaries']
    xs = [.005, .26, .515, .77]
    for i, (x, label) in enumerate(zip(xs, labels)):
        box(ax, x, .17, .225, .68, label, fc='#EAF2F8', ec='#4C78A8', fs=10)
        if i < 3:
            arrow(ax, (x + .23, .51), (xs[i + 1] - .005, .51))
    ax = diagram(fig, (.015, .025, .97, .43), 'B', 'Empirical application and software reuse')
    box(ax, .005, .08, .475, .82, 'Acute pancreatitis (AP)\nClinical-data application\nReference comparison\nCohorts and observed outcomes', fc='#FFF4E6', ec=P['P3'], fs=10.5)
    box(ax, .52, .08, .475, .82, 'Acute kidney injury (AKI)\nSynthetic-data example\nEvidence and execution\ninterfaces reused', fc='#E8F5E9', ec='#2A9D8F', fs=10.5)
    export(fig, 'Figure_6_Generic_Framework')


if __name__ == '__main__':
    functions = [figure1, figure2, figure3, figure4, figure5, figure6]
    selected = [int(x) for x in sys.argv[1].split(',')] if len(sys.argv) > 1 and sys.argv[1] != '--all' else list(range(1, 7))
    for index in selected:
        functions[index - 1]()
    if '--all' in sys.argv:
        from supplementary_layout import supplementary_figure1, supplementary_figure2, graphical_abstract
        supplementary_figure1()
        supplementary_figure2()
        graphical_abstract()
