import tempfile,subprocess, pathlib, shutil,os,re
repo=pathlib.Path(__file__).resolve().parents[1]; root=pathlib.Path(tempfile.mkdtemp(prefix='step63-exact-')); print('scratch',root,flush=True)
subprocess.run('git archive 1ddeaf2 | tar -x -C "$DIR"',cwd=repo,shell=True,env={**os.environ,'DIR':str(root)},check=True)
env={**os.environ,'PYTHONPATH':':'.join(str(root/x) for x in ['services/calculation-engine','services/api','packages/domain-model','packages/geometry','packages/reporting','packages/standards-data']), 'PYTHONDONTWRITEBYTECODE':'1'}
def run(name,path,commit,reference,target,replacement,tests):
 hist=subprocess.check_output(['git','show',f'{commit}^:{path}'],cwd=repo,text=True)
 p=root/path; src=p.read_text()
 assert reference in hist,(name,'missing historical reference');assert src.count(target)==1,(name,'target count',src.count(target))
 p.write_text(src.replace(target,replacement,1))
 result=subprocess.run([str(repo/'.venv/bin/pytest'),'-q']+['tests/'+f for f in tests],cwd=root,env=env,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True)
 lines=result.stdout.splitlines();print(name,'exit=',result.returncode,'summary=',[l for l in lines if re.search(r'\d+ (?:failed|passed|error)',l) and ' in ' in l][-1:],'failures=',[l for l in lines if l.startswith(('FAILED ','ERROR '))],flush=True);p.write_text(src)
 if result.returncode != 1 or not any(l.startswith('FAILED ') for l in lines): raise AssertionError(f'{name}: expected failing tests')
try:
 risk='services/calculation-engine/aegislps_engine/risk.py'
 old='        l_f = 0.1 * inputs.fire_risk_rf * (0.5 if inputs.has_automatic_fire_system else 1.0) * t_occupancy'
 run('H3',risk,'44ec813',old,'        l_f = loss_vals.l_f1 * t_occupancy',old,['test_risk_factors_2024.py'])
 lemp='services/calculation-engine/aegislps_engine/lemp_engine.py'
 old='        kms = 1.0'
 target='            kms = float(10.0 ** (-sf_db / 20.0))\n            safety_distance_m = _safety_distance_dsf_m(shield.mesh_width_w_m, sf_db)\n            k_source = _K_SOURCE_IEC_2024'
 run('C3-b',lemp,'6719bb9',old,target,'            kms = 1.0\n            safety_distance_m = _safety_distance_dsf_m(shield.mesh_width_w_m, sf_db)\n            k_source = _K_SOURCE_IEC_2024',['test_lemp_induction_physics.py'])
 spd='services/calculation-engine/aegislps_engine/spd_coordination.py'
 old='        l_max = (uw_kv - up_kv) * 10.0 # meters\n        return float(max(5.0, min(30.0, l_max)))'
 target='        """Compute maximum SPD connecting-lead length ``L_max`` [m] from Eq. (C.1)–(C.4)."""'
 run('H15',spd,'b1114b2',old,target,target+'\n        uw_kv = u_req_kv  # adaptation: current signature uses u_req_kv\n'+old,['test_spd_coordination_annex_c.py'])
finally:
 shutil.rmtree(root);print('scratch removed=',not root.exists(),flush=True)
