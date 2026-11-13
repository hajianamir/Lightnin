import os, tempfile, subprocess, pathlib, shutil, re
repo=pathlib.Path(__file__).resolve().parents[1]; root=pathlib.Path(tempfile.mkdtemp(prefix='step63-exact-')); print('scratch',root,flush=True)
subprocess.run('git archive 1ddeaf2 | tar -x -C "$DIR"',shell=True,cwd=repo,env={**os.environ,'DIR':str(root)},check=True)
env={**os.environ,'PYTHONPATH':':'.join(str(root/x) for x in ['services/calculation-engine','services/api','packages/domain-model','packages/geometry','packages/reporting','packages/standards-data']), 'PYTHONDONTWRITEBYTECODE':'1'}
def old(commit,path): return subprocess.check_output(['git','show',commit+'^:'+path],cwd=repo,text=True)
def case(name,path,fix,old_fragment,new_fragment,tests):
 p=root/path; original=p.read_text(); historical=old(fix,path)
 if old_fragment not in historical: raise AssertionError(f'{name}: original fragment absent')
 if original.count(new_fragment)!=1: raise AssertionError(f'{name}: target is not unique')
 p.write_text(original.replace(new_fragment,old_fragment,1))
 proc=subprocess.run([str(repo/'.venv/bin/pytest'),'-q']+['tests/'+x for x in tests],cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT)
 failures=[x for x in proc.stdout.splitlines() if x.startswith('FAILED ') or x.startswith('ERROR ')]
 summary=[x for x in proc.stdout.splitlines() if re.search(r'\d+ (failed|passed|errors?)',x) and (' in ' in x)]
 print(name,'exit=',proc.returncode, 'summary=',summary[-1:] ,'failures=',failures,flush=True)
 p.write_text(original)
 if proc.returncode != 1 or not any(x.startswith('FAILED ') for x in failures): raise AssertionError(f'{name}: expected failing tests')
try:
 geo='packages/geometry/aegislps_geometry/rolling_sphere.py'; eng='services/calculation-engine/aegislps_engine/'
 case('C1',geo,'2e3188a','        z_protect = rod_height_m - (self.r - np.sqrt(max(0.0, self.r**2 - d_horiz**2)))\n\n        is_protected = point_z <= z_protect', '        max_axial_protected_z = min(h_val, 2.0 * r_val - h_val)\n        is_protected = (\n            z_val <= h_val\n            and d_horiz <= rho_allowed\n            and (rho_allowed > 0.0 or (d_horiz == 0.0 and z_val <= max_axial_protected_z))\n        )', ['test_rolling_sphere_reference.py','test_optimization_conservative.py'])
 touch=eng+'touch_step.py'
 frag='        if inp.has_physical_insulation_barrier:\n            prospective_touch = 0.0\n            prospective_step = min(prospective_step, u_step_tol * 0.5)\n        if inp.has_restricted_access_perimeter:\n            prospective_touch = 0.0\n            prospective_step = 0.0\n\n        touch_controlled = prospective_touch <= u_touch_tol'
 case('C2',touch,'19a607a',frag,'        touch_controlled = prospective_touch <= u_touch_tol',['test_touch_step_physics.py'])
 lemp=eng+'lemp_engine.py'
 frag='            tau1 = 10.0 # us\n            tau2 = 350.0 # us'
 target='        tau1 = params["tau1"]\n        tau2 = params["tau2"]'
 # Insert exactly historical statements under existing branch; use historical test in scratch.
 original=(root/lemp).read_text(); hist=old('1347b14',lemp); assert frag in hist and original.count(target)==1
 adapted='        if stroke_type == "first_positive_10_350":\n'+frag+'\n        else:\n            tau1 = params["tau1"]\n            tau2 = params["tau2"]'
 (root/lemp).write_text(original.replace(target,adapted)); r=subprocess.run([str(repo/'.venv/bin/pytest'),'-q','tests/test_lemp_heidler_physics.py','tests/test_lemp_induction_physics.py'],cwd=root,env=env,text=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT); print('C3 exit=',r.returncode,'summary=',[x for x in r.stdout.splitlines() if re.search(r'\d+ failed',x) and ' in ' in x][-1:], 'failures=',[x for x in r.stdout.splitlines() if x.startswith('FAILED ')],flush=True); (root/lemp).write_text(original)
 if r.returncode != 1 or not any(x.startswith('FAILED ') for x in r.stdout.splitlines()): raise AssertionError('C3: expected failing tests')
 case('C4',geo,'ec571e8','    "III": 200.0,','    "III": 45.0,',['test_rolling_sphere_edition2024.py'])
 earth=eng+'earthing.py';case('C4-b',earth,'3343007','            return float(min(20.0, max(5.0, 20.0 * (rho / 800.0)))) if rho >= 100.0 else 5.0','            return 5.0 if rho_f <= 500.0 else float(0.03 * rho_f - 10.0)',['test_minimum_length_l1_figure5.py'])
 case('H4',earth,'16fa0ed','            r_single = (rho / (2.0 * np.pi * l_rod)) * (np.log(4.0 * l_rod / r_cond) - 1.0)\n\n            # Mutual coupling array efficiency factor eta (IEEE 80 / Tagg model)\n            # eta ~ (1 + alpha * (L / s)) / N\n            if n_rods > 1:\n                coupling_factor = (l_rod / (2.0 * np.pi * s_spacing)) * np.log(1.0 + (s_spacing / l_rod))\n                r_dc = float((r_single / n_rods) * (1.0 + (n_rods - 1) * coupling_factor))\n            else:\n                r_dc = float(r_single)','            r_dc = array_resistance_identical_rods(rho, l_rod, r_cond, n_rods, s_spacing)',['test_multi_rod_mutual.py'])
 case('H5',earth,'dcc070d','            term1 = np.log((8.0 * d_ring) / r_cond)\n            term2 = np.log((4.0 * d_ring) / h_depth)\n            r_dc = float((rho / (2.0 * (np.pi ** 2) * d_ring)) * (term1 + term2))','            r_dc = float(\n                (rho / ((np.pi ** 2) * d_ring))\n                * np.log((4.0 * d_ring) / equiv_radius)\n            )',['test_earthing_ring_strip.py'])
 angle='packages/geometry/aegislps_geometry/protective_angle.py';case('H8',angle,'3343007','(20.0, 25.0)','(20.0, 22.4)',['test_protective_angle_figure1.py'])
 risk=eng+'risk.py'; case('H9',risk,'73c7cdc','    lps_class: str = "I"  # Class I, II, III, IV, or none','    lps_class: str  # Required: one of {"none", "I", "II", "III", "IV"}',['test_advanced_modules.py', 'test_api_error_mapping.py', 'test_bom_pv_hvi_opt_peec_nodal_b6.py', 'test_earth_pit_and_rod_sizing.py', 'test_earthing_and_spd.py', 'test_earthing_ring_strip.py', 'test_earthing_spd_earth_b3.py', 'test_geometry_domain_b5.py', 'test_lemp_engine.py', 'test_lemp_heidler_physics.py', 'test_lemp_induction_physics.py', 'test_mesh_method_and_hvi.py', 'test_minimum_length_l1_figure5.py', 'test_multi_rod_mutual.py', 'test_nodal_solver.py', 'test_optimization_and_pv.py', 'test_optimization_conservative.py', 'test_peec_and_mesh_rolling_sphere.py', 'test_project_io.py', 'test_risk_factors_2024.py', 'test_risk_inputs_b2.py', 'test_separation_distance.py', 'test_spd_coordination_annex_c.py', 'test_touch_lemp_uq_b4.py', 'test_touch_step_physics.py', 'test_uq_engine.py'])
 # Remaining H3/H15 require interface adaptation that is recorded separately.
finally:
 shutil.rmtree(root);print('scratch removed=',not root.exists(),flush=True)
